import sys
import os
import logging
import asyncio
import timeit
import tracemalloc
from collections import Counter

from config import LOG_FILE_PATH, LOG_FORMAT, LOG_DATE_FORMAT, LOG_LEVEL
from database import DatabaseManager, DatabaseError
from processor import read_and_process, detect_anomalies, save_files_with_threads, poll_all_stations
from monitoring import measure_memory, compare_approaches, profile_function

# Setup logging — writes to both terminal and log file
os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.DEBUG),
    format=LOG_FORMAT,
    datefmt=LOG_DATE_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)


def main():
    print("\nDigital Twin Analytics - Smart Manufacturing")
    print("-" * 50)

    db = DatabaseManager()

    # Step 1 - Check database connection
    print("\nStep 1 - Checking database...")
    if not db.check_health():
        print("Database not ready. Check MySQL and .env settings.")
        sys.exit(1)
    print("Database is healthy")

    # Step 2 - Read and process sensor data
    # Using tracemalloc to track memory usage during processing
    print("\nStep 2 - Reading and processing sensor data...")
    data = measure_memory(read_and_process, label="read_and_process")
    print(f"Processed {len(data)} sensor readings")

    # Step 3 - Detect anomalies
    print("\nStep 3 - Detecting anomalies...")
    anomalies = detect_anomalies(data)
    print(f"Detected {len(anomalies)} anomalies")

    counts = Counter(a["station_id"] for a in anomalies)
    print("Anomalies per station:")
    for station, count in counts.most_common():
        print(f"  {station:20} - {count}")

    # Step 4 - Save CSV and JSON using 2 threads
    print("\nStep 4 - Saving data to CSV and JSON...")
    save_files_with_threads(data)
    print("Files saved using 2 threads")

    # Step 5 - Insert data into MySQL using batch inserts
    print("\nStep 5 - Inserting data into MySQL...")
    db.insert_sensor_readings(data)
    db.insert_anomalies(anomalies)
    print("Data inserted into MySQL")

    # Step 6 - Run SQL analytics queries
    print("\nStep 6 - Running SQL analytics queries...")

    print("\n  Query 1 - Station Summary (JOIN + GROUP BY):")
    for row in db.get_station_summary():
        print(f"    {row['station_id']:15} - readings: {row['total_readings']} "
              f"- failures: {row['total_failures']} - avg torque: {row['avg_torque']} Nm")

    print("\n  Query 2 - Failure Rate per Station (CTE):")
    for row in db.get_failure_rate():
        print(f"    {row['station_id']:15} - {row['failure_rate_pct']}% - {row['risk_level']}")

    print("\n  Query 3 - Daily Production (GROUP BY + HAVING):")
    for row in db.get_daily_production()[:5]:
        print(f"    {str(row['production_date']):12} - "
              f"readings: {row['total_readings']} - failures: {row['daily_failures']}")

    print("\n  Query 4 - Rolling Average Torque (Window Function):")
    for row in db.get_rolling_avg_torque()[:5]:
        print(f"    {row['station_id']:15} - torque: {row['torque_nm']} "
              f"- rolling avg: {row['rolling_avg_torque']}")

    # Step 7 - Performance comparison O(n2) vs O(n)
    print("\nStep 7 - Performance comparison...")

    station_list = [r["station_id"] for r in data]
    small = station_list[:500]

    def count_slow(lst):
        # O(n2) — bad approach, nested loop
        result = {}
        for item in lst:
            result[item] = lst.count(item)
        return result

    def count_fast(lst):
        # O(n) — good approach using Counter
        return dict(Counter(lst))

    compare_approaches(
        count_slow, count_fast,
        args1=(small,), args2=(small,),
        runs=3
    )

    # Step 8 - Profile the anomaly detection function using cProfile
    print("\nStep 8 - Profiling anomaly detection...")
    profile_function(detect_anomalies, data[:500])
    print("cProfile done - check logs for details")

    # Step 9 - Async polling of all 6 stations
    print("\nStep 9 - Polling all stations asynchronously...")
    results = asyncio.run(poll_all_stations())
    for r in results:
        print(f"  {r['station_id']:20} - {r['status']}")

    print("\n" + "-" * 50)
    print("Pipeline complete")
    print(f"  Sensor readings inserted : {len(data)}")
    print(f"  Anomalies detected       : {len(anomalies)}")
    print(f"  Threads used             : 2")
    print(f"  Stations polled async    : {len(results)}")
    print("-" * 50)
    print("\nRun dashboard: streamlit run dashboard/app.py\n")
    logger.info("Pipeline completed successfully")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Stopped by user")
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        print(f"Error: {e}")
        sys.exit(1)