import logging
import mysql.connector
from contextlib import contextmanager
from config import DB_CONFIG

logger = logging.getLogger(__name__)


# Custom exception for database errors
class DatabaseError(Exception):
    pass


class DatabaseManager:
    """Handles all MySQL database operations."""

    def get_connection(self):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            logger.debug("Connected to database")
            return conn
        except mysql.connector.Error as e:
            logger.error("Connection failed: %s", e)
            raise DatabaseError(f"Cannot connect to MySQL: {e}")

    @contextmanager
    def get_cursor(self):
        # Context manager — auto commits, rolls back on error, always closes
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error("Query failed, rolled back: %s", e)
            raise
        finally:
            cursor.close()
            conn.close()
            logger.debug("Connection closed")

    def insert_sensor_readings(self, readings):
        if not readings:
            return 0

        query = """
            INSERT INTO sensor_readings (
                udi, product_id, product_type, station_id,
                air_temp_k, process_temp_k, rotational_speed,
                torque_nm, tool_wear_min, machine_failure,
                shift, timestamp
            ) VALUES (
                %(udi)s, %(product_id)s, %(product_type)s, %(station_id)s,
                %(air_temp_k)s, %(process_temp_k)s, %(rotational_speed)s,
                %(torque_nm)s, %(tool_wear_min)s, %(machine_failure)s,
                %(shift)s, %(timestamp)s
            )
        """
        total = 0
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Insert in batches of 500 — faster than inserting one by one
            for i in range(0, len(readings), 500):
                batch = readings[i:i + 500]
                cursor.executemany(query, batch)
                conn.commit()
                total += len(batch)
                logger.info("Inserted %d rows so far", total)
        except mysql.connector.Error as e:
            conn.rollback()
            raise DatabaseError(f"Insert failed: {e}")
        finally:
            cursor.close()
            conn.close()
        return total

    def insert_anomalies(self, anomalies):
        if not anomalies:
            return 0

        query = """
            INSERT INTO anomalies (
                udi, station_id, failure_type, failure_desc,
                sensor_name, actual_value, threshold_value, severity
            ) VALUES (
                %(udi)s, %(station_id)s, %(failure_type)s, %(failure_desc)s,
                %(sensor_name)s, %(actual_value)s, %(threshold_value)s,
                %(severity)s
            )
        """
        with self.get_cursor() as cursor:
            cursor.executemany(query, anomalies)
        logger.info("Inserted %d anomalies", len(anomalies))
        return len(anomalies)

    # Query 1 — JOIN: sensor_readings + stations table
    def get_station_summary(self):
        query = """
            SELECT
                sr.station_id,
                st.station_name,
                st.robot_model,
                COUNT(*) AS total_readings,
                SUM(sr.machine_failure) AS total_failures,
                ROUND(AVG(sr.torque_nm), 2) AS avg_torque,
                ROUND(AVG(sr.tool_wear_min), 2) AS avg_tool_wear,
                ROUND(AVG(sr.air_temp_k - 273.15), 2) AS avg_temp_celsius
            FROM sensor_readings sr
            INNER JOIN stations st ON sr.station_id = st.station_id
            GROUP BY sr.station_id, st.station_name, st.robot_model
            ORDER BY total_failures DESC
        """
        with self.get_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    # Query 2 — CTE: failure rate per station
    def get_failure_rate(self):
        query = """
            WITH stats AS (
                SELECT station_id,
                       COUNT(*) AS total,
                       SUM(machine_failure) AS failures
                FROM sensor_readings
                GROUP BY station_id
            )
            SELECT station_id,
                   total,
                   failures,
                   ROUND(failures * 100.0 / total, 2) AS failure_rate_pct,
                   CASE
                       WHEN failures * 100.0 / total > 3 THEN 'HIGH RISK'
                       ELSE 'NORMAL'
                   END AS risk_level
            FROM stats
            ORDER BY failure_rate_pct DESC
        """
        with self.get_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    # Query 3 — Window Function: rolling average torque per station
    def get_rolling_avg_torque(self):
        query = """
            SELECT station_id,
                   timestamp,
                   torque_nm,
                   ROUND(AVG(torque_nm) OVER (
                       PARTITION BY station_id
                       ORDER BY timestamp
                       ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
                   ), 2) AS rolling_avg_torque
            FROM sensor_readings
            ORDER BY station_id, timestamp
            LIMIT 100
        """
        with self.get_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    # Query 4 — GROUP BY date with HAVING
    def get_daily_production(self):
        query = """
            SELECT DATE(timestamp) AS production_date,
                   COUNT(*) AS total_readings,
                   SUM(machine_failure) AS daily_failures
            FROM sensor_readings
            GROUP BY DATE(timestamp)
            HAVING total_readings > 50
            ORDER BY production_date
        """
        with self.get_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def get_all_anomalies(self):
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM anomalies ORDER BY detected_at DESC")
            return cursor.fetchall()

    def check_health(self):
        # Check all 3 required tables exist
        required = {"stations", "sensor_readings", "anomalies"}
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SHOW TABLES")
                existing = {list(row.values())[0] for row in cursor.fetchall()}
                missing = required - existing
                if missing:
                    logger.error("Missing tables: %s", missing)
                    return False
                logger.info("Database health check passed")
                return True
        except Exception as e:
            logger.error("Health check failed: %s", e)
            return False