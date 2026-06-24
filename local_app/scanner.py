from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path

from config import get_config
from state_store import load_root_assets, load_tags, load_vendor_groups


MARKER_RE = re.compile(
    r"(^|[^a-z0-9])(materials?|textures?|prefabs?|fbx|animations?|animator|anim|models?|meshes?|shaders?|matcap|tex|mat)([^a-z0-9]|$)",
    re.IGNORECASE,
)


@dataclass
class AssetNode:
    id: str
    vendor: str
    asset: str
    path: str
    depth: int
    status: str
    reason: str
    tag: str = ""
    child_count: int = 0
    marker_dirs: list[str] | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _dirs(path: Path) -> list[Path]:
    try:
        return sorted([item for item in path.iterdir() if item.is_dir()], key=lambda item: item.name.lower())
    except OSError:
        return []


def _marker_dirs(path: Path) -> list[str]:
    return [item.name for item in _dirs(path) if MARKER_RE.search(item.name)]


def _all_markerish(children: list[Path]) -> bool:
    return bool(children) and all(MARKER_RE.search(child.name) for child in children)


def _item_id(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def scan_assets() -> list[dict]:
    cfg = get_config()
    if not cfg.assets_root.strip():
        return []

    root = Path(cfg.assets_root)
    assigned_tags = load_tags()
    forced_root_assets = load_root_assets()
    forced_vendor_groups = load_vendor_groups()
    tag_names = {tag.name for tag in cfg.tags}
    ignored = {name.lower() for name in cfg.ignored_top_folders}

    if not root.exists():
        return []

    nodes: list[AssetNode] = []

    def add_asset(path: Path, vendor: str, reason: str) -> None:
        item_id = _item_id(root, path)
        nodes.append(AssetNode(
            id=item_id,
            vendor=vendor,
            asset=path.name,
            path=str(path),
            depth=len(path.relative_to(root).parts),
            status="confirmed",
            reason=reason,
            tag=assigned_tags.get(item_id, ""),
            child_count=len(_dirs(path)),
            marker_dirs=_marker_dirs(path),
        ))

    for top in _dirs(root):
        if top.name in tag_names or top.name.lower() in ignored:
            continue

        children = _dirs(top)
        top_markers = _marker_dirs(top)
        top_id = _item_id(root, top)

        if top_id in forced_vendor_groups:
            for child in children:
                add_asset(child, top.name, "manual_vendor_group")
            continue

        if top_id in forced_root_assets:
            add_asset(top, "", "manual_root_asset")
            continue

        if _all_markerish(children):
            add_asset(top, "", "marker_children_only")
            continue

        if not children:
            add_asset(top, "", "top_level_leaf")
            continue

        if top_markers:
            add_asset(top, "", "mixed_marker_and_asset_children")
            continue

        for child in children:
            add_asset(child, top.name, "vendor_asset")

    return [node.to_dict() for node in nodes]
