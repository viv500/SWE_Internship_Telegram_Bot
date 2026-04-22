import json
import os
from config import STATE_FILE, MAX_TRACKED_PER_SOURCE


def load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[WARNING] Could not load state file, resetting: {e}")
        return {}


def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_seen_ids(state: dict, source_name: str) -> set:
    return set(state.get(source_name, []))


def mark_seen(state: dict, source_name: str, new_ids: list) -> dict:
    existing = state.get(source_name, [])
    existing_set = set(existing)  # O(1) lookups instead of O(n) list scans
    combined = existing + [i for i in new_ids if i not in existing_set]
    state[source_name] = combined[-MAX_TRACKED_PER_SOURCE:]
    return state
