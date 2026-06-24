from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from config import APP_DIR, UNTAGGED_TAG_NAME, get_config
from scanner import scan_assets
from state_store import remove_tag


LOG_PATH = APP_DIR / "move_log.jsonl"


def _sanitize(name: str) -> str:
    invalid = '<>:"/\\|?*'
    cleaned = "".join("_" if char in invalid else char for char in name).strip()
    return cleaned or "미분류"


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    if path.is_file() or path.suffix:
        for index in range(1, 1000):
            candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
            if not candidate.exists():
                return candidate
    for index in range(1, 1000):
        candidate = path.with_name(f"{path.name}_{index}")
        if not candidate.exists():
            return candidate
    raise FileExistsError(f"Too many duplicate folders: {path}")


def _meta_path(path: Path) -> Path:
    return Path(str(path) + ".meta")


def _move_meta(source: Path, target: Path) -> list[dict]:
    source_meta = _meta_path(source)
    if not source_meta.exists():
        return []
    target_meta = _meta_path(target)
    if target_meta.exists():
        source_meta.unlink(missing_ok=True)
        return [{"from": str(source_meta), "to": str(target_meta), "status": "dropped_duplicate_meta"}]
    shutil.move(str(source_meta), str(target_meta))
    return [{"from": str(source_meta), "to": str(target_meta)}]


def _remove_empty_top_folder(root: Path, source: Path) -> list[dict]:
    try:
        top = root / source.relative_to(root).parts[0]
    except (IndexError, ValueError):
        return []
    if top == root or not top.exists():
        return []
    try:
        next(top.iterdir())
        return []
    except StopIteration:
        top.rmdir()
        operations = [{"from": str(top), "status": "removed_empty_top_folder"}]
        top_meta = _meta_path(top)
        if top_meta.exists():
            top_meta.unlink()
            operations.append({"from": str(top_meta), "status": "removed_empty_top_meta"})
        return operations
    except OSError:
        return []


def _merge_move(source: Path, target: Path) -> list[dict]:
    operations: list[dict] = []
    target.mkdir(parents=True, exist_ok=True)
    for child in source.iterdir():
        destination = target / child.name
        if child.is_dir():
            operations.extend(_merge_move(child, destination))
        else:
            final_destination = destination if not destination.exists() else _unique_path(destination)
            shutil.move(str(child), str(final_destination))
            operations.append({"from": str(child), "to": str(final_destination)})
    try:
        source.rmdir()
    except OSError:
        pass
    operations.extend(_move_meta(source, target))
    return operations


def _target_for(root: Path, node: dict, tag: str) -> Path:
    safe_tag = _sanitize(tag)
    safe_asset = _sanitize(node["asset"])
    if tag == UNTAGGED_TAG_NAME:
        if node.get("vendor"):
            return root / _sanitize(node["vendor"]) / safe_asset
        return root / safe_asset
    if node.get("vendor"):
        return root / safe_tag / _sanitize(node["vendor"]) / safe_asset
    return root / safe_tag / safe_asset


def organize(item_ids: list[str]) -> list[dict]:
    cfg = get_config()
    root = Path(cfg.assets_root)
    nodes = {node["id"]: node for node in scan_assets()}
    results = []

    for item_id in item_ids:
        node = nodes.get(item_id)
        if not node:
            results.append({"id": item_id, "error": "not found"})
            continue
        tag = node.get("tag", "").strip()
        if not tag:
            results.append({"id": item_id, "error": "tag required"})
            continue

        source = Path(node["path"])
        target = _target_for(root, node, tag)
        if not source.exists():
            results.append({"id": item_id, "error": "source missing"})
            continue
        if source == target:
            results.append({"id": item_id, "status": "skipped", "reason": "already there"})
            continue

        operations = _merge_move(source, target) if target.exists() else []
        if not operations:
            target.parent.mkdir(parents=True, exist_ok=True)
            final_target = target if not target.exists() else _unique_path(target)
            shutil.move(str(source), str(final_target))
            operations = [{"from": str(source), "to": str(final_target)}]
            operations.extend(_move_meta(source, final_target))
        operations.extend(_remove_empty_top_folder(root, source))

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "id": item_id,
            "tag": tag,
            "vendor": node.get("vendor", ""),
            "asset": node.get("asset", ""),
            "operations": operations,
        }
        with LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        remove_tag(item_id)
        results.append({"id": item_id, "status": "moved", "operations": operations})

    return results
