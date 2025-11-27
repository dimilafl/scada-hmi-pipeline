import time
from datetime import datetime, timezone

import requests
from pymodbus.client.sync import ModbusTcpClient


MODBUS_HOST = "127.0.0.1"
MODBUS_PORT = 5020

API_BASE = "http://127.0.0.1:8000"


def scale_register_to_float(raw):
    # Simple fixed scale: value = raw / 10.0
    return raw / 10.0


def update_point(tag: str, value: float):
    payload = {
        "value": value,
        "quality": "GOOD",
    }
    try:
        resp = requests.post(f"{API_BASE}/api/points/{tag}", json=payload, timeout=2.0)
        resp.raise_for_status()
        print(f"[{datetime.now(timezone.utc).isoformat()}] Updated {tag} -> {value}")
    except Exception as e:
        print(f"Error updating {tag}: {e}")


def main():
    client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
    if not client.connect():
        print("Failed to connect to Modbus server")
        return

    try:
        while True:
            # Read 2 holding registers starting at address 0
            rr = client.read_holding_registers(0, 2, unit=1)
            if rr.isError():
                print(f"Modbus error: {rr}")
            else:
                pt101_raw = rr.registers[0]
                ft201_raw = rr.registers[1]

                pt101_value = scale_register_to_float(pt101_raw)
                ft201_value = scale_register_to_float(ft201_raw)

                update_point("PT_101", pt101_value)
                update_point("FT_201", ft201_value)

            time.sleep(2.0)
    finally:
        client.close()


if __name__ == "__main__":
    main()
