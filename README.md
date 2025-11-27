# Minimal SCADA HMI → Point DB → Tag-Binding Pipeline

## Overview

This project recreates a minimal SCADA data path in software, demonstrating the core concepts of industrial control systems:

- **JSON point database** defining engineering metadata (tag names, data types, engineering units, limits, alarm thresholds)
- **Mock SCADA REST API** exposing points and supporting operator writes
- **Simple HMI** that polls the API, shows tag values, quality indicators, and alarms

This implementation provides a clear mental model of how real SCADA systems manage process data, from sensor inputs through the point database to graphical displays.

## How to Run

### Setup Virtual Environment

```bash
python -m venv .venv

# Windows PowerShell:
.venv\Scripts\Activate.ps1

# or Windows cmd:
.venv\Scripts\activate.bat

# or bash/Linux/macOS:
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install fastapi uvicorn
```

### Start the Server

```bash
uvicorn main:app --reload
```

### Access the Application

- **API Endpoint**: http://127.0.0.1:8000/api/points
- **HMI Interface**: http://127.0.0.1:8000/static/hmi.html

## Architecture

The project consists of these key components:

- **`points_schema.json`** – Point metadata (tag name, datatype, eng units, limits, alarm thresholds)
- **`points_state.json`** – Live state (value, quality, timestamp) for each tag
- **`main.py`** – Mock SCADA API using FastAPI:
  - `GET /api/points` – Retrieve all points with current values and alarm states
  - `GET /api/points/{tag}` – Retrieve a single point
  - `POST /api/points/{tag}` – Update a point value (operator command)
- **`static/hmi.html`** – Minimal HMI table and controls
- **`static/hmi.js`** – Tag-binding logic: polls `/api/points`, colors rows by quality/alarm, sends valve commands

## SCADA Concept Mapping

This project maps core SCADA concepts to simple software implementations:

- **Tags** → JSON-defined points in `points_schema.json` + `points_state.json`. Each tag represents a process variable (pressure, flow, valve state, etc.)

- **Quality** → `GOOD` vs non-GOOD status, used for row coloring and basic data validity checking. In real SCADA systems, quality indicates whether sensor data is trustworthy.

- **Alarms** → Computed in `main.py` from each point's `alarm_low` / `alarm_high` limits. When values exceed thresholds, the alarm state changes and the HMI reflects this visually.

- **HMI binding** → JavaScript in `static/hmi.js` polling `/api/points`, updating DOM rows, and reflecting state/alarms visually. This simulates how real HMI software subscribes to tag changes and updates graphics.

## Testing the Workflow

1. **View initial state**: Open the HMI and observe the three points (PT_101, FT_201, VALVE_1_CMD)

2. **Send operator command**: Click "Open Valve" or "Close Valve" buttons to write to `VALVE_1_CMD`

3. **Trigger alarms**: Edit `points_state.json` and set `PT_101.value` to `1300.0` (above `alarm_high` of 1200.0). Save and watch the row turn red on the next poll.

4. **Test quality indicators**: Change any point's `quality` field to `BAD` and observe the row color change.

## Next Expansions

Future enhancements could include:

- Replace REST with Modbus/DNP3 mock protocol
- Add trend charts with historical data visualization
- Support additional point types (INT, ENUM, STRING)
- Implement user authentication and access control
- Add event logging and alarm acknowledgment
