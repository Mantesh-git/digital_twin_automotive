# config.py
"""
Central configuration — all settings in one place.
Every other module imports from here.
Covers: Type hints, constants, environment variables
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Database ──────────────────────────────────
DB_CONFIG: dict = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "").strip("'\""),
    "database": os.getenv("DB_NAME", "digital_twin_automotive"),
    "port":     int(os.getenv("DB_PORT", 3306)),
}

# ── File Paths ────────────────────────────────
RAW_DATA_PATH: str       = "data/raw/ai4i2020.csv"
PROCESSED_CSV_PATH: str  = "data/processed/sensor_readings.csv"
PROCESSED_JSON_PATH: str = "data/processed/sensor_readings.json"
LOG_FILE_PATH: str       = "logs/digital_twin.log"

# ── Stations ──────────────────────────────────
STATIONS: tuple = (
    "STAMPING",
    "WELDING",
    "PAINTING",
    "ENGINE_MOUNT",
    "QUALITY_CHECK",
    "FINAL_ASSEMBLY",
)

STATION_NAMES: dict = {
    "STAMPING":       "Stamping Press Robot",
    "WELDING":        "Welding Robot",
    "PAINTING":       "Paint Spray Robot",
    "ENGINE_MOUNT":   "Engine Mounting Robot",
    "QUALITY_CHECK":  "Quality Inspection Robot",
    "FINAL_ASSEMBLY": "Final Assembly Robot",
}

STATION_SEQUENCE: dict = {
    "STAMPING":       1,
    "WELDING":        2,
    "PAINTING":       3,
    "ENGINE_MOUNT":   4,
    "QUALITY_CHECK":  5,
    "FINAL_ASSEMBLY": 6,
}

STATION_ROBOTS: dict = {
    "STAMPING":       "FANUC R-2000iC",
    "WELDING":        "KUKA KR 16",
    "PAINTING":       "ABB IRB 5500",
    "ENGINE_MOUNT":   "FANUC M-2000iA",
    "QUALITY_CHECK":  "COGNEX IS7000",
    "FINAL_ASSEMBLY": "KUKA KR 210",
}

# ── Shifts ────────────────────────────────────
SHIFTS: tuple = ("MORNING", "AFTERNOON", "NIGHT")

# ── Anomaly Thresholds ────────────────────────
THRESHOLDS: dict = {
    "torque_nm":        {"warning": 60.0,  "critical": 70.0},
    "tool_wear_min":    {"warning": 180,   "critical": 200},
    "air_temp_k":       {"warning": 302.0, "critical": 304.0},
    "process_temp_k":   {"warning": 311.0, "critical": 313.0},
    "rotational_speed": {"warning": 2600,  "critical": 2800},
}

# ── Failure Types ─────────────────────────────
FAILURE_TYPES: dict = {
    "TWF": "Tool Wear Failure",
    "HDF": "Heat Dissipation Failure",
    "PWF": "Power Failure",
    "OSF": "Overstrain Failure",
    "RNF": "Random Failure",
}

FAILURE_SEVERITY: dict = {
    "TWF": "MEDIUM",
    "HDF": "HIGH",
    "PWF": "HIGH",
    "OSF": "MEDIUM",
    "RNF": "LOW",
}

# ── Processing ────────────────────────────────
BATCH_SIZE: int       = 500
LOG_EVERY_N_ROWS: int = 1000

# ── Logging ───────────────────────────────────
LOG_LEVEL: str       = os.getenv("LOG_LEVEL", "DEBUG")
LOG_FORMAT: str      = "%(asctime)s | %(levelname)-8s | %(module)-15s | %(message)s"
LOG_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"