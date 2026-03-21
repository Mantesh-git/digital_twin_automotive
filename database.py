# database.py
"""
Module 2 — Database Manager
=============================
Covers trainer topics:
- Context managers with statement (topic 3.7)
- Custom exceptions (topic 3.6)
- SQL joins, aggregations, window functions, CTEs (topic 6)
- Type hints (topic 3.5)
- Custom class — DatabaseManager (topic 3.4)
- SOLID Single Responsibility — only handles DB operations
"""

import mysql.connector
from mysql.connector.connection import MySQLConnection
from contextlib import contextmanager
from typing import Optional, Generator
import sys
from config import DB_CONFIG
from logging_setup import get_logger

logger = get_logger(__name__)


# ──────────────────────────────────────────
# Custom Exceptions (trainer topic 3.6)
# ──────────────────────────────────────────

class DatabaseError(Exception):
    """Base exception for all database errors."""
    pass


class DBConnectionError(DatabaseError):
    """Raised when MySQL connection cannot be established."""
    def __init__(self):
        super().__init__(
            f"Cannot connect to MySQL at "
            f"{DB_CONFIG['host']}:{DB_CONFIG['port']}. "
            f"Check .env file and ensure MySQL is running."
        )


class DBQueryError(DatabaseError):
    """Raised when a SQL query fails during execution."""
    def __init__(self, query_name: str, reason: str):
        super().__init__(
            f"Query '{query_name}' failed: {reason}"
        )


# ──────────────────────────────────────────
# DatabaseManager Class
# ──────────────────────────────────────────

class DatabaseManager:
    """
    Handles all MySQL database operations for Digital Twin.

    SOLID — Single Responsibility Principle:
    This class ONLY handles database operations.
    It does NOT read CSV files, detect anomalies, or log metrics.

    Methods:
    - get_connection()         → create MySQL connection
    - get_cursor()             → context manager for safe operations
    - insert_sensor_readings() → batch insert 10,000 rows
    - insert_anomalies()       → store detected anomalies
    - get_station_summary()    → JOIN query
    - get_failure_rate()       → CTE query
    - get_rolling_avg_torque() → Window function query
    - get_daily_production()   → GROUP BY date query
    - get_anomaly_summary()    → JOIN anomalies + stations
    - check_health()           → verify DB is ready
    """

    # ──────────────────────────────────────
    # CONNECTION
    # ──────────────────────────────────────

    def get_connection(self) -> MySQLConnection:
        """
        Create and return a MySQL connection using DB_CONFIG from config.py

        Returns:
            MySQLConnection: Active database connection

        Raises:
            DBConnectionError: If connection fails — FAIL FAST
            (system cannot work without DB)
        """
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            logger.debug("MySQL connected to '%s'", DB_CONFIG["database"])
            return conn
        except mysql.connector.Error as e:
            logger.error("MySQL connection failed: %s", str(e))
            raise DBConnectionError()

    # ──────────────────────────────────────
    # CONTEXT MANAGER (trainer topic 3.7)
    # ──────────────────────────────────────

    @contextmanager
    def get_cursor(self) -> Generator:
        """
        Safe context manager for all DB operations.

        Trainer topic 3.7 — Context Managers:
        Guarantees:
        ✅ Auto commits on success
        ✅ Auto rolls back on any error
        ✅ Always closes connection — no resource leaks

        Usage:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM stations")
                results = cursor.fetchall()

        Yields:
            cursor: MySQL cursor (returns rows as dicts)

        Raises:
            DBQueryError: If any DB operation fails
        """
        conn: Optional[MySQLConnection] = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            yield cursor
            conn.commit()
            logger.debug("Transaction committed successfully")

        except DBConnectionError:
            raise  # already logged — re-raise as is

        except mysql.connector.Error as e:
            if conn:
                conn.rollback()
                logger.warning("Transaction rolled back: %s", str(e))
            raise DBQueryError("cursor_operation", str(e))

        finally:
            if conn and conn.is_connected():
                conn.close()
                logger.debug("DB connection closed")

    # ──────────────────────────────────────
    # INSERT — SENSOR READINGS
    # ──────────────────────────────────────

    def insert_sensor_readings(self, readings: list[dict]) -> int:
        """
        Batch insert all sensor readings into MySQL.

        Why batches of 500?
        - 10,000 rows one by one = 10,000 DB round trips (slow)
        - 10,000 rows in 500 batches = 20 round trips (fast)
        - Trade-off: slightly more memory per batch vs speed

        Args:
            readings: List of processed sensor reading dicts

        Returns:
            int: Total number of rows inserted

        Raises:
            DBQueryError: If insert fails
        """
        if not readings:
            logger.warning("No readings to insert — empty list")
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

        total: int = 0
        batch_size: int = 500
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            for i in range(0, len(readings), batch_size):
                batch = readings[i : i + batch_size]
                cursor.executemany(query, batch)
                conn.commit()
                total += len(batch)
                logger.info(
                    "Inserted batch %d/%d — total so far: %d rows",
                    (i // batch_size) + 1,
                    -(-len(readings) // batch_size),
                    total
                )
        except mysql.connector.Error as e:
            conn.rollback()
            logger.error("Batch insert failed: %s", str(e))
            raise DBQueryError("insert_sensor_readings", str(e))
        finally:
            cursor.close()
            conn.close()

        logger.info("✅ All %d sensor readings inserted", total)
        return total

    # ──────────────────────────────────────
    # INSERT — ANOMALIES
    # ──────────────────────────────────────

    def insert_anomalies(self, anomalies: list[dict]) -> int:
        """
        Insert detected anomalies into anomalies table.

        Args:
            anomalies: List of anomaly dicts from processor.py

        Returns:
            int: Number of anomalies inserted
        """
        if not anomalies:
            logger.info("No anomalies to insert")
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

        logger.info("✅ Inserted %d anomalies", len(anomalies))
        return len(anomalies)

    # ──────────────────────────────────────
    # SQL ANALYTICS QUERIES
    # Trainer topic 6 — all patterns covered
    # ──────────────────────────────────────

    def get_station_summary(self) -> list[dict]:
        """
        Query 1 — INNER JOIN + GROUP BY + Aggregation

        Joins sensor_readings with stations table.
        Shows total readings, failures, avg torque per station.
        """
        query = """
            SELECT
                sr.station_id,
                st.station_name,
                st.robot_model,
                COUNT(*)                            AS total_readings,
                SUM(sr.machine_failure)             AS total_failures,
                ROUND(AVG(sr.torque_nm), 2)         AS avg_torque,
                ROUND(AVG(sr.tool_wear_min), 2)     AS avg_tool_wear,
                ROUND(AVG(sr.air_temp_k - 273.15), 2) AS avg_temp_celsius
            FROM sensor_readings sr
            INNER JOIN stations st
                ON sr.station_id = st.station_id
            GROUP BY
                sr.station_id, st.station_name, st.robot_model
            ORDER BY total_failures DESC
        """
        with self.get_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def get_failure_rate(self) -> list[dict]:
        """
        Query 2 — CTE (WITH clause)

        Calculates failure rate % per station.
        High risk = failure_rate > 3%
        """
        query = """
            WITH station_stats AS (
                SELECT
                    station_id,
                    COUNT(*)            AS total_readings,
                    SUM(machine_failure) AS total_failures
                FROM sensor_readings
                GROUP BY station_id
            )
            SELECT
                station_id,
                total_readings,
                total_failures,
                ROUND(total_failures * 100.0 / total_readings, 2)
                    AS failure_rate_pct,
                CASE
                    WHEN total_failures * 100.0 / total_readings > 3
                    THEN 'HIGH RISK'
                    ELSE 'NORMAL'
                END AS risk_level
            FROM station_stats
            ORDER BY failure_rate_pct DESC
        """
        with self.get_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def get_rolling_avg_torque(self) -> list[dict]:
        """
        Query 3 — Window Function (OVER PARTITION BY)

        Rolling average torque over last 10 readings per station.
        Shows wear trends — if rolling avg rises, station is struggling.
        """
        query = """
            SELECT
                station_id,
                timestamp,
                torque_nm,
                ROUND(
                    AVG(torque_nm) OVER (
                        PARTITION BY station_id
                        ORDER BY timestamp
                        ROWS BETWEEN 9 PRECEDING AND CURRENT ROW
                    ), 2
                ) AS rolling_avg_torque
            FROM sensor_readings
            ORDER BY station_id, timestamp
            LIMIT 500
        """
        with self.get_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def get_daily_production(self) -> list[dict]:
        """
        Query 4 — GROUP BY date + HAVING

        Daily production count with failure trend.
        Only shows days with more than 50 readings.
        """
        query = """
            SELECT
                DATE(timestamp)         AS production_date,
                COUNT(*)                AS total_readings,
                SUM(machine_failure)    AS daily_failures,
                ROUND(AVG(torque_nm), 2) AS avg_torque,
                ROUND(AVG(tool_wear_min), 2) AS avg_tool_wear
            FROM sensor_readings
            GROUP BY DATE(timestamp)
            HAVING total_readings > 50
            ORDER BY production_date
        """
        with self.get_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def get_anomaly_summary(self) -> list[dict]:
        """
        Query 5 — JOIN anomalies + stations + GROUP BY

        Shows which stations have most anomalies
        and what type/severity they are.
        """
        query = """
            SELECT
                a.station_id,
                st.station_name,
                a.failure_type,
                a.severity,
                COUNT(*) AS anomaly_count
            FROM anomalies a
            INNER JOIN stations st
                ON a.station_id = st.station_id
            GROUP BY
                a.station_id, st.station_name,
                a.failure_type, a.severity
            ORDER BY anomaly_count DESC
        """
        with self.get_cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def get_all_readings(self) -> list[dict]:
        """Fetch all sensor readings — used by dashboard."""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM sensor_readings ORDER BY timestamp"
            )
            return cursor.fetchall()

    def get_all_anomalies(self) -> list[dict]:
        """Fetch all anomalies — used by dashboard."""
        with self.get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM anomalies ORDER BY detected_at DESC"
            )
            return cursor.fetchall()

    # ──────────────────────────────────────
    # HEALTH CHECK
    # ──────────────────────────────────────

    def check_health(self) -> bool:
        """
        Verify DB connection and all 4 tables exist.

        Returns:
            bool: True if everything is ready
        """
        required_tables = {
            "stations",
            "sensor_readings",
            "anomalies",
            "production_shifts"
        }
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SHOW TABLES")
                existing = {
                    list(row.values())[0]
                    for row in cursor.fetchall()
                }
                missing = required_tables - existing
                if missing:
                    logger.error("Missing tables: %s", missing)
                    return False
                logger.info("DB health check passed — all tables present")
                return True
        except (DBConnectionError, DBQueryError) as e:
            logger.error("Health check failed: %s", str(e))
            return False


# ──────────────────────────────────────────
# Quick test — run directly to verify
# ──────────────────────────────────────────
if __name__ == "__main__":
    print("\n🔍 Testing DatabaseManager...\n")

    db = DatabaseManager()

    # Test 1 — Connection
    try:
        conn = db.get_connection()
        conn.close()
        print("✅ Test 1 — Connection: PASSED")
    except DBConnectionError as e:
        print(f"❌ Test 1 — Connection: FAILED\n   {e}")
        sys.exit(1)

    # Test 2 — Health Check
    healthy = db.check_health()
    print(
        f"{'✅' if healthy else '❌'} "
        f"Test 2 — Health Check: "
        f"{'PASSED' if healthy else 'FAILED'}"
    )

    # Test 3 — Stations
    with db.get_cursor() as cursor:
        cursor.execute(
            "SELECT station_id, station_name FROM stations "
            "ORDER BY sequence_no"
        )
        stations = cursor.fetchall()
    print(f"\n✅ Test 3 — Found {len(stations)} stations:")
    for s in stations:
        print(f"   {s['station_id']:15} → {s['station_name']}")

    print("\n🎉 database.py ready! Proceed to processor.py\n")