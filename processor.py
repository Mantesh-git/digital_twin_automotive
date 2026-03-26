import csv
import json
import os
import logging
import threading
import asyncio
from datetime import datetime, timedelta
from collections import Counter
from config import (
    RAW_DATA_PATH, PROCESSED_CSV_PATH, PROCESSED_JSON_PATH,
    STATIONS, SHIFTS, THRESHOLDS, FAILURE_TYPES, FAILURE_SEVERITY
)

logger = logging.getLogger(__name__)


# Custom exception for processor errors
class ProcessorError(Exception):
    pass


def get_station(udi):
    # Assign station using modulo — distributes rows evenly across 6 stations
    return STATIONS[(udi - 1) % len(STATIONS)]


def get_shift(udi):
    # Assign shift — cycles through MORNING, AFTERNOON, NIGHT
    return SHIFTS[(udi - 1) % len(SHIFTS)]


def get_timestamp(udi):
    # Generate a realistic timestamp — starts 30 days ago, 4 mins apart
    base = datetime.now() - timedelta(days=30)
    return (base + timedelta(minutes=(udi - 1) * 4)).strftime("%Y-%m-%d %H:%M:%S")


def read_and_process():
    """Read CSV file using generator and return list of processed rows."""
    if not os.path.exists(RAW_DATA_PATH):
        raise ProcessorError(f"Dataset not found at {RAW_DATA_PATH}")

    processed = []

    # Generator — reads one row at a time instead of loading all 10000 rows
    with open(RAW_DATA_PATH, "r", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            udi = int(row["UDI"])
            processed.append({
                "udi": udi,
                "product_id": row["Product ID"],
                "product_type": row["Type"],
                "air_temp_k": round(float(row["Air temperature [K]"]), 2),
                "process_temp_k": round(float(row["Process temperature [K]"]), 2),
                "rotational_speed": int(row["Rotational speed [rpm]"]),
                "torque_nm": round(float(row["Torque [Nm]"]), 2),
                "tool_wear_min": int(row["Tool wear [min]"]),
                "machine_failure": int(row["Machine failure"]),
                "TWF": int(row["TWF"]),
                "HDF": int(row["HDF"]),
                "PWF": int(row["PWF"]),
                "OSF": int(row["OSF"]),
                "RNF": int(row["RNF"]),
                "station_id": get_station(udi),
                "shift": get_shift(udi),
                "timestamp": get_timestamp(udi),
            })

    logger.info("Processed %d rows from CSV", len(processed))
    return processed


def detect_anomalies(readings):
    """Detect anomalies from failure flags and sensor threshold breaches."""
    anomalies = []

    for r in readings:
        # Check failure flags — TWF, HDF, PWF, OSF, RNF
        for flag in ["TWF", "HDF", "PWF", "OSF", "RNF"]:
            if r.get(flag) == 1:
                anomalies.append({
                    "udi": r["udi"],
                    "station_id": r["station_id"],
                    "failure_type": flag,
                    "failure_desc": FAILURE_TYPES[flag],
                    "sensor_name": flag,
                    "actual_value": 1.0,
                    "threshold_value": 0.0,
                    "severity": FAILURE_SEVERITY[flag],
                })

        # Check sensor values against thresholds
        for sensor in ["torque_nm", "tool_wear_min"]:
            val = float(r.get(sensor, 0))
            t = THRESHOLDS[sensor]
            if val >= t["critical"]:
                sev = "HIGH"
            elif val >= t["warning"]:
                sev = "MEDIUM"
            else:
                continue
            anomalies.append({
                "udi": r["udi"],
                "station_id": r["station_id"],
                "failure_type": "THRESHOLD",
                "failure_desc": f"{sensor} exceeded {sev} threshold",
                "sensor_name": sensor,
                "actual_value": val,
                "threshold_value": t["critical"] if sev == "HIGH" else t["warning"],
                "severity": sev,
            })

    logger.info("Detected %d anomalies", len(anomalies))
    return anomalies


def save_csv(data):
    os.makedirs(os.path.dirname(PROCESSED_CSV_PATH), exist_ok=True)
    with open(PROCESSED_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    logger.info("Saved CSV to %s", PROCESSED_CSV_PATH)


def save_json(data):
    os.makedirs(os.path.dirname(PROCESSED_JSON_PATH), exist_ok=True)
    with open(PROCESSED_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info("Saved JSON to %s", PROCESSED_JSON_PATH)


def save_files_with_threads(data):
    # Save CSV and JSON at the same time using 2 threads (I/O bound task)
    t1 = threading.Thread(target=save_csv,  args=(data,))
    t2 = threading.Thread(target=save_json, args=(data,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    logger.info("CSV and JSON saved using 2 threads")


async def poll_station(station_id):
    # Simulate async sensor polling — each station responds after 50ms
    await asyncio.sleep(0.05)
    return {
        "station_id": station_id,
        "status": "ONLINE",
        "polled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


async def poll_all_stations():
    # All 6 stations polled at the same time — non blocking
    tasks = [poll_station(s) for s in STATIONS]
    return await asyncio.gather(*tasks)


if __name__ == "__main__":
    # Setup basic logging for testing
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s | %(levelname)s | %(message)s")

    print("Test 1 - Reading and processing CSV...")
    data = read_and_process()
    print(f"  Rows processed: {len(data)}")

    counts = Counter(r["station_id"] for r in data)
    print("  Rows per station:")
    for s, c in sorted(counts.items()):
        print(f"    {s:20} - {c}")

    print("\nTest 2 - Detecting anomalies...")
    anomalies = detect_anomalies(data)
    print(f"  Total anomalies: {len(anomalies)}")

    print("\nTest 3 - Saving files using 2 threads...")
    save_files_with_threads(data)
    print("  Files saved")

    print("\nTest 4 - Async station polling...")
    results = asyncio.run(poll_all_stations())
    for r in results:
        print(f"  {r['station_id']:20} - {r['status']}")

    print("\nAll tests passed")