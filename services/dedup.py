import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.getenv("DEDUP_STORE_PATH", "processed_message_ids.json")
STORE_PATH = env_path if os.path.isabs(env_path) else os.path.join(BASE_DIR, env_path)


def _load() -> set:
    if not os.path.exists(STORE_PATH) or os.path.getsize(STORE_PATH) == 0:
        return set()
    try:
        with open(STORE_PATH) as f:
            return set(json.load(f))
    except json.JSONDecodeError:
        return set()


def _save(ids: set) -> None:
    with open(STORE_PATH, "w") as f:
        json.dump(list(ids), f)


def is_already_processed(message_id: str) -> bool:
    return message_id in _load()


def mark_processed(message_id: str) -> None:
    ids = _load()
    ids.add(message_id)
    _save(ids)


def clear_dedup_store() -> None:
    _save(set())
