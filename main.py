from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime, timezone
import json
import os

SCHEMA_PATH = "points_schema.json"
STATE_PATH = "points_state.json"
HISTORY_DIR = "history"

app = FastAPI()

# CORS for local dev / browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static HMI files
app.mount("/static", StaticFiles(directory="static"), name="static")


# ---------- Data models ----------

class PointUpdate(BaseModel):
    value: Any
    quality: str = "GOOD"


# ---------- Helper functions ----------

def load_schema() -> Dict[str, Any]:
    with open(SCHEMA_PATH, "r") as f:
        schema_list = json.load(f)
    # index by tag for quick lookup
    return {p["tag"]: p for p in schema_list}


def load_state() -> Dict[str, Any]:
    if not os.path.exists(STATE_PATH):
        return {}
    with open(STATE_PATH, "r") as f:
        return json.load(f)


def save_state(state: Dict[str, Any]) -> None:
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def compute_alarm_state(tag: str, value: Any, schema: Dict[str, Any]) -> str:
    meta = schema.get(tag)
    if not meta:
        return "UNKNOWN"

    # Only numeric alarms for now
    if meta["datatype"] != "float":
        return "NORMAL"

    try:
        v = float(value)
    except (ValueError, TypeError):
        return "INVALID"

    low = meta.get("alarm_low")
    high = meta.get("alarm_high")

    if low is not None and v < low:
        return "ALARM_LOW"
    if high is not None and v > high:
        return "ALARM_HIGH"
    return "NORMAL"


def ensure_history_dir():
    os.makedirs(HISTORY_DIR, exist_ok=True)


def history_file_for_tag(tag: str) -> str:
    ensure_history_dir()
    # Simple per-tag JSON file
    safe_tag = tag.replace("/", "_")
    return os.path.join(HISTORY_DIR, f"{safe_tag}.json")


def append_history_record(tag: str, record: Dict[str, Any]) -> None:
    path = history_file_for_tag(tag)
    try:
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
        else:
            data = []
    except Exception:
        data = []

    data.append(record)
    # keep only the last 500 samples per tag to avoid unbounded growth
    if len(data) > 500:
        data = data[-500:]

    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def read_history(tag: str, limit: int = 50) -> Dict[str, Any]:
    path = history_file_for_tag(tag)
    if not os.path.exists(path):
        return {"tag": tag, "samples": []}

    try:
        with open(path, "r") as f:
            data = json.load(f)
    except Exception:
        data = []

    # return most recent first
    samples = data[-limit:]
    return {
        "tag": tag,
        "samples": samples
    }


# ---------- API endpoints ----------

@app.get("/api/points")
def get_all_points():
    schema = load_schema()
    state = load_state()

    result = []
    for tag, meta in schema.items():
        pt_state = state.get(tag, {})
        value = pt_state.get("value")
        quality = pt_state.get("quality", "BAD")
        ts = pt_state.get("timestamp")
        alarm_state = compute_alarm_state(tag, value, schema)

        result.append({
            "tag": tag,
            "description": meta["description"],
            "datatype": meta["datatype"],
            "eng_unit": meta["eng_unit"],
            "value": value,
            "quality": quality,
            "timestamp": ts,
            "alarm_state": alarm_state,
            "limits": {
                "low": meta.get("low_limit"),
                "high": meta.get("high_limit"),
                "alarm_low": meta.get("alarm_low"),
                "alarm_high": meta.get("alarm_high"),
            }
        })
    return {"points": result}


@app.get("/api/points/{tag}")
def get_point(tag: str):
    schema = load_schema()
    if tag not in schema:
        raise HTTPException(status_code=404, detail="Unknown tag")

    state = load_state()
    pt_state = state.get(tag, {})
    value = pt_state.get("value")
    quality = pt_state.get("quality", "BAD")
    ts = pt_state.get("timestamp")

    alarm_state = compute_alarm_state(tag, value, schema)

    meta = schema[tag]
    return {
        "tag": tag,
        "description": meta["description"],
        "datatype": meta["datatype"],
        "eng_unit": meta["eng_unit"],
        "value": value,
        "quality": quality,
        "timestamp": ts,
        "alarm_state": alarm_state,
        "limits": {
            "low": meta.get("low_limit"),
            "high": meta.get("high_limit"),
            "alarm_low": meta.get("alarm_low"),
            "alarm_high": meta.get("alarm_high"),
        }
    }


@app.post("/api/points/{tag}")
def update_point(tag: str, update: PointUpdate):
    schema = load_schema()
    if tag not in schema:
        raise HTTPException(status_code=404, detail="Unknown tag")

    state = load_state()
    now = datetime.now(timezone.utc).isoformat()

    state[tag] = {
        "value": update.value,
        "quality": update.quality,
        "timestamp": now
    }

    save_state(state)

    alarm_state = compute_alarm_state(tag, update.value, schema)

    # append to historian
    append_history_record(tag, {
        "timestamp": now,
        "value": update.value,
        "quality": update.quality,
        "alarm_state": alarm_state,
    })

    return {
        "tag": tag,
        "value": update.value,
        "quality": update.quality,
        "timestamp": now,
        "alarm_state": alarm_state
    }


@app.get("/api/history/{tag}")
def get_history(tag: str, limit: int = 50):
    # Simple historian read
    try:
        result = read_history(tag, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading history for {tag}: {e}")
    return result
