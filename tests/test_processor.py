import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processor import get_station, get_shift, detect_anomalies, ProcessorError


def test_station_mapping():
    assert get_station(1) == "STAMPING"
    assert get_station(2) == "WELDING"
    assert get_station(3) == "PAINTING"
    assert get_station(4) == "ENGINE_MOUNT"
    assert get_station(5) == "QUALITY_CHECK"
    assert get_station(6) == "FINAL_ASSEMBLY"
    assert get_station(7) == "STAMPING"  # cycles back
    print("Test 1 - Station mapping: PASSED")


def test_shift_mapping():
    assert get_shift(1) == "MORNING"
    assert get_shift(2) == "AFTERNOON"
    assert get_shift(3) == "NIGHT"
    assert get_shift(4) == "MORNING"  # cycles back
    print("Test 2 - Shift mapping: PASSED")


def test_anomaly_detection():
    sample = [
        {
            "udi": 1, "station_id": "WELDING",
            "torque_nm": 75.0,     # above critical threshold 70
            "tool_wear_min": 50,
            "machine_failure": 1,
            "TWF": 1, "HDF": 0, "PWF": 0, "OSF": 0, "RNF": 0
        },
        {
            "udi": 2, "station_id": "STAMPING",
            "torque_nm": 30.0,     # normal — below warning threshold
            "tool_wear_min": 10,
            "machine_failure": 0,
            "TWF": 0, "HDF": 0, "PWF": 0, "OSF": 0, "RNF": 0
        }
    ]
    anomalies = detect_anomalies(sample)
    assert len(anomalies) > 0
    stations = [a["station_id"] for a in anomalies]
    assert "WELDING" in stations
    assert "STAMPING" not in stations
    print(f"Test 3 - Anomaly detection: PASSED ({len(anomalies)} anomalies found)")


def test_no_anomalies():
    # All normal readings — should return empty list
    sample = [
        {
            "udi": 1, "station_id": "STAMPING",
            "torque_nm": 30.0,
            "tool_wear_min": 10,
            "machine_failure": 0,
            "TWF": 0, "HDF": 0, "PWF": 0, "OSF": 0, "RNF": 0
        }
    ]
    anomalies = detect_anomalies(sample)
    assert len(anomalies) == 0
    print("Test 4 - No anomalies on normal data: PASSED")


def test_processor_error():
    try:
        raise ProcessorError("test error")
    except ProcessorError as e:
        assert "test error" in str(e)
    print("Test 5 - ProcessorError exception: PASSED")


if __name__ == "__main__":
    print("Running tests...\n")
    test_station_mapping()
    test_shift_mapping()
    test_anomaly_detection()
    test_no_anomalies()
    test_processor_error()
    print("\nAll 5 tests passed")