# Digital Twin Analytics for Smart Manufacturing

A Python-based Digital Twin system that virtually monitors 6 robotic stations in an automotive assembly line. It processes 10,000 real sensor readings, detects anomalies, stores data in MySQL, runs SQL analytics queries, and displays insights on a Streamlit dashboard.

---

## Project Details

| Item | Details |
|---|---|
| Trainee | Mahantesh Hosmani |
| Dataset | AI4I 2020 Predictive Maintenance Dataset (UCI) |
| Database | MySQL — digital_twin_manufacturing |
| Language | Python 3.14 |

---

## Folder Structure

```
digital_twin_automotive/
│
├── config.py                   # All settings, constants and thresholds
├── database.py                 # MySQL connection and SQL queries
├── processor.py                # CSV processing, anomaly detection, threading, async
├── monitoring.py               # timeit, tracemalloc, cProfile
├── main.py                     # Entry point — runs all modules in sequence
│
├── dashboard/
│   └── app.py                  # Streamlit frontend dashboard
│
├── tests/
│   └── test_processor.py       # 5 unit tests for core logic
│
├── data/
│   ├── raw/
│   │   └── ai4i2020.csv        # Original dataset (10,000 rows)
│   ├── processed/
│   │   ├── sensor_readings.csv # Processed output
│   │   └── sensor_readings.json
│   └── factory.jpg             # Dashboard image
│
├── logs/
│   └── digital_twin.log        # Runtime logs
│
├── .env                        # Database credentials (not in GitHub)
├── .gitignore
└── requirements.txt
```

---

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.14 |
| Database | MySQL 8.0 |
| Frontend | Streamlit |
| Dataset | AI4I 2020 UCI |
| Version Control | Git + GitHub |
| Performance | timeit, tracemalloc, cProfile |
| Concurrency | threading, asyncio |

---

## Setup Instructions

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Mantesh-git/digital_twin_automotive.git
cd digital_twin_automotive
```

### Step 2 — Install Dependencies

```bash
pip install mysql-connector-python python-dotenv pandas streamlit plotly
```

### Step 3 — Create .env File

Create a `.env` file in the root folder with your MySQL credentials:

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=digital_twin_manufacturing
DB_PORT=3306
LOG_LEVEL=DEBUG
```

### Step 4 — Setup MySQL Database

Open MySQL Workbench and run:

```sql
CREATE DATABASE digital_twin_manufacturing;
USE digital_twin_manufacturing;

CREATE TABLE stations (
    station_id   VARCHAR(20)  PRIMARY KEY,
    station_name VARCHAR(100) NOT NULL,
    robot_model  VARCHAR(100) NOT NULL,
    sequence_no  INT          NOT NULL,
    created_at   DATETIME     DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sensor_readings (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    udi              INT         NOT NULL,
    product_id       VARCHAR(20) NOT NULL,
    product_type     CHAR(1)     NOT NULL,
    station_id       VARCHAR(20) NOT NULL,
    air_temp_k       FLOAT       NOT NULL,
    process_temp_k   FLOAT       NOT NULL,
    rotational_speed INT         NOT NULL,
    torque_nm        FLOAT       NOT NULL,
    tool_wear_min    INT         NOT NULL,
    machine_failure  TINYINT(1)  DEFAULT 0,
    shift            VARCHAR(10) NOT NULL,
    timestamp        DATETIME    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (station_id) REFERENCES stations(station_id)
);

CREATE TABLE anomalies (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    udi             INT          NOT NULL,
    station_id      VARCHAR(20)  NOT NULL,
    detected_at     DATETIME     DEFAULT CURRENT_TIMESTAMP,
    failure_type    VARCHAR(10)  NOT NULL,
    failure_desc    VARCHAR(100) NOT NULL,
    sensor_name     VARCHAR(50),
    actual_value    FLOAT,
    threshold_value FLOAT,
    severity        ENUM('LOW','MEDIUM','HIGH') NOT NULL,
    FOREIGN KEY (station_id) REFERENCES stations(station_id)
);

CREATE INDEX idx_station ON sensor_readings(station_id);
CREATE INDEX idx_failure ON sensor_readings(machine_failure);
CREATE INDEX idx_severity ON anomalies(severity);

INSERT INTO stations (station_id, station_name, robot_model, sequence_no) VALUES
('STAMPING',       'Stamping Press Robot',     'FANUC R-2000iC',  1),
('WELDING',        'Welding Robot',            'KUKA KR 16',      2),
('PAINTING',       'Paint Spray Robot',        'ABB IRB 5500',    3),
('ENGINE_MOUNT',   'Engine Mounting Robot',    'FANUC M-2000iA',  4),
('QUALITY_CHECK',  'Quality Inspection Robot', 'COGNEX IS7000',   5),
('FINAL_ASSEMBLY', 'Final Assembly Robot',     'KUKA KR 210',     6);
```

### Step 5 — Place Dataset

Download the AI4I 2020 dataset and place it at:
```
data/raw/ai4i2020.csv
```

---

## How to Run

### Run Full Pipeline

```bash
python main.py
```

This runs all 9 steps:
1. Database health check
2. Read and process 10,000 sensor readings
3. Detect anomalies
4. Save CSV and JSON using 2 threads
5. Insert data into MySQL
6. Run 5 SQL analytics queries
7. Performance comparison O(n2) vs O(n)
8. Profile anomaly detection using cProfile
9. Async poll all 6 stations

### Run Dashboard

```bash
streamlit run dashboard/app.py
```

Opens at http://localhost:8501

### Run Unit Tests

```bash
python tests/test_processor.py
```

### Clear MySQL Data Before Re-Running

```sql
USE digital_twin_manufacturing;
TRUNCATE TABLE anomalies;
TRUNCATE TABLE sensor_readings;
```

---

## The 6 Robot Stations

| Station | Robot Model | Job |
|---|---|---|
| STAMPING | FANUC R-2000iC | Stamps metal into body panels |
| WELDING | KUKA KR 16 | Welds body panels together |
| PAINTING | ABB IRB 5500 | Spray paints the car body |
| ENGINE_MOUNT | FANUC M-2000iA | Mounts engine into body |
| QUALITY_CHECK | COGNEX IS7000 | Inspects for defects |
| FINAL_ASSEMBLY | KUKA KR 210 | Installs doors, seats, electronics |

---

## SQL Queries

| Query | Type | Purpose |
|---|---|---|
| get_station_summary | JOIN + GROUP BY | Failures and avg torque per station |
| get_failure_rate | CTE (WITH) | Failure % — HIGH RISK if above 3% |
| get_rolling_avg_torque | Window Function | Rolling avg torque over 10 readings |
| get_daily_production | GROUP BY + HAVING | Daily production count and failures |
| get_anomaly_summary | JOIN | Anomaly count by type and severity |

---

## Key Results

| Metric | Value |
|---|---|
| Sensor readings processed | 10,000 |
| Anomalies detected | 2,332 |
| Highest failure station | WELDING — 3.72% — HIGH RISK |
| Only NORMAL station | STAMPING — 2.94% |
| Memory used (peak) | 7,180 KB |
| Performance improvement | count_fast is 41x faster than count_slow |
| Threads used | 2 |
| Stations polled async | 6 |
| Unit tests passing | 5 out of 5 |

---

## Python Concepts Demonstrated

| Concept | Where Used |
|---|---|
| Generator | processor.py — reads CSV one row at a time |
| Context Manager | database.py — get_cursor() auto commits and closes |
| Threading | processor.py — saves CSV and JSON simultaneously |
| Async / Await | processor.py — polls 6 stations at once |
| Counter | processor.py — counts anomalies per station |
| Custom Exceptions | database.py — DatabaseError, processor.py — ProcessorError |
| timeit | monitoring.py — measures execution speed |
| tracemalloc | monitoring.py — tracks memory usage |
| cProfile | monitoring.py — finds slowest functions |
| Tuple (immutable) | config.py — STATIONS cannot be modified |
| Logging | main.py — DEBUG, INFO, WARNING, ERROR levels |

---

## Module Overview

### config.py
Stores all project settings in one place — database credentials, station names, sensor thresholds, failure types and logging configuration. All other modules import from here. Follows the DRY principle.

### database.py
Handles all MySQL operations. Uses a context manager for safe database transactions that auto-commits on success and rolls back on error. Contains 5 SQL queries covering JOIN, CTE, Window Functions, GROUP BY and HAVING.

### processor.py
The core module. Reads CSV using a generator (memory efficient), maps each row to one of 6 stations using modulo, detects anomalies using failure flags and threshold rules, saves files using 2 threads simultaneously, and polls stations using async.

### monitoring.py
Performance measurement module. Uses timeit to measure execution speed, tracemalloc to track memory usage, and cProfile to identify the slowest functions in the code.

### main.py
Entry point that orchestrates all modules in 9 sequential steps. Handles logging setup, error handling with custom exceptions, and graceful shutdown on keyboard interrupt.

### dashboard/app.py
Streamlit frontend that reads from MySQL and displays a factory image, KPI metrics, station summary table, bar chart of failures, failure rate table, daily production trend chart, and a filterable anomaly table.

### tests/test_processor.py
5 unit tests verifying station mapping, shift mapping, anomaly detection on abnormal data, no anomalies on normal data, and custom exception behaviour.

---

## Git Workflow

```
main branch        ← stable, production-ready code
  └── develop      ← working branch, all features committed here
        └── PR     ← develop merged into main via Pull Request
```

---

## Author

Mahantesh Hosmani
Graduate Engineer Trainee - trumetric.ai
