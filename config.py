import os
from dotenv import load_dotenv

load_dotenv()

# Database connection settings
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "").strip("'\""),
    "database": os.getenv("DB_NAME", "digital_twin_manufacturing"),
    "port":     int(os.getenv("DB_PORT", 3306)),
}

# File paths
RAW_DATA_PATH       = "data/raw/ai4i2020.csv"
PROCESSED_CSV_PATH  = "data/processed/sensor_readings.csv"
PROCESSED_JSON_PATH = "data/processed/sensor_readings.json"
LOG_FILE_PATH       = "logs/digital_twin.log"

# 6 robot stations in the assembly line
# Using tuple because this list should never change
STATIONS = (
    "STAMPING",
    "WELDING",
    "PAINTING",
    "ENGINE_MOUNT",
    "QUALITY_CHECK",
    "FINAL_ASSEMBLY",
)

# Work shifts
SHIFTS = ("MORNING", "AFTERNOON", "NIGHT")

# Sensor thresholds for anomaly detection
THRESHOLDS = {
    "torque_nm":     {"warning": 60.0, "critical": 70.0},
    "tool_wear_min": {"warning": 180,  "critical": 200},
}

# Failure type codes from the dataset
FAILURE_TYPES = {
    "TWF": "Tool Wear Failure",
    "HDF": "Heat Dissipation Failure",
    "PWF": "Power Failure",
    "OSF": "Overstrain Failure",
    "RNF": "Random Failure",
}

# Severity level for each failure type
FAILURE_SEVERITY = {
    "TWF": "MEDIUM",
    "HDF": "HIGH",
    "PWF": "HIGH",
    "OSF": "MEDIUM",
    "RNF": "LOW",
}

# Logging settings
LOG_LEVEL       = os.getenv("LOG_LEVEL", "DEBUG")
LOG_FORMAT      = "%(asctime)s | %(levelname)s | %(module)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"