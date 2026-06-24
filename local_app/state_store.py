from __future__ import annotations

import json
from pathlib import Path

from config import APP_DIR


STATE_PATH = APP_DIR / "classifier_state.json"


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {"tags": {}, "root_assets": [], "vendor_groups": []}
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"tags": {}, "root_assets": [], "vendor_groups": []}
        if "tags" not in data:
            return {"tags": data, "root_assets": [], "vendor_groups": []}
        data.setdefault("tags", {})
        data.setdefault("root_assets", [])
        data.setdefault("vendor_groups", [])
        return data
    except Exception:
        return {"tags": {}, "root_assets": [], "vendor_groups": []}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def load_tags() -> dict[str, str]:
    return load_state()["tags"]


def load_root_assets() -> set[str]:
    return set(load_state().get("root_assets", []))


def load_vendor_groups() -> set[str]:
    return set(load_state().get("vendor_groups", []))


def set_tag(item_id: str, tag: str) -> None:
    state = load_state()
    if tag:
        state["tags"][item_id] = tag
    else:
        state["tags"].pop(item_id, None)
    save_state(state)


def set_root_asset(item_id: str) -> None:
    state = load_state()
    root_assets = set(state.get("root_assets", []))
    vendor_groups = set(state.get("vendor_groups", []))
    if item_id:
        root_assets.add(item_id)
        vendor_groups.discard(item_id)
    state["root_assets"] = sorted(root_assets)
    state["vendor_groups"] = sorted(vendor_groups)
    save_state(state)


def set_vendor_group(item_id: str) -> None:
    state = load_state()
    root_assets = set(state.get("root_assets", []))
    vendor_groups = set(state.get("vendor_groups", []))
    if item_id:
        vendor_groups.add(item_id)
        root_assets.discard(item_id)
    state["root_assets"] = sorted(root_assets)
    state["vendor_groups"] = sorted(vendor_groups)
    save_state(state)


def remove_tag(item_id: str) -> None:
    state = load_state()
    state["tags"].pop(item_id, None)
    save_state(state)
