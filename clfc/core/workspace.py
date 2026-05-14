from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from clfc.core.index import ResolveError, resolve_record
from clfc.utils.hashing import workspace_hash

WORKSPACE_SCHEMA_VERSION = 1


class WorkspaceError(ValueError):
    pass


def clfc_dir(workspace: Path) -> Path:
    return workspace.expanduser().resolve() / ".clfc"


def workspace_json_path(workspace: Path) -> Path:
    return clfc_dir(workspace) / "workspace.json"


def init_workspace(workspace: Path) -> dict[str, Any]:
    workspace = workspace.expanduser().resolve()
    path = workspace_json_path(workspace)
    existing = load_workspace(workspace, required=False)
    now = _now()
    payload = existing or {}
    payload.update(
        {
            "schema_version": WORKSPACE_SCHEMA_VERSION,
            "workspace_path": str(workspace),
            "workspace_hash": workspace_hash(workspace),
            "updated_at": now,
        }
    )
    payload.setdefault("created_at", now)
    payload.setdefault("active_session_id", None)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def load_workspace(workspace: Path, required: bool = True) -> dict[str, Any] | None:
    path = workspace_json_path(workspace)
    if not path.exists():
        if required:
            raise WorkspaceError(f"Workspace is not initialized. Run `clfc init` in {workspace.expanduser().resolve()}.")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as error:
        raise WorkspaceError(f"Invalid workspace metadata at {path}: {error}") from error
    if not isinstance(payload, dict):
        raise WorkspaceError(f"Invalid workspace metadata at {path}: expected a JSON object.")
    return payload


def set_active_session(workspace: Path, record: dict[str, Any]) -> dict[str, Any]:
    payload = init_workspace(workspace)
    payload["active_session_id"] = str(record.get("session_id") or "")
    payload["active_display_name"] = record.get("display_name")
    payload["active_updated_at"] = record.get("updated_at")
    payload["updated_at"] = _now()
    workspace_json_path(workspace).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def clear_active_session(workspace: Path) -> dict[str, Any]:
    payload = load_workspace(workspace)
    assert payload is not None
    payload["active_session_id"] = None
    payload.pop("active_display_name", None)
    payload.pop("active_updated_at", None)
    payload["updated_at"] = _now()
    workspace_json_path(workspace).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def active_session_id(workspace: Path) -> str | None:
    payload = load_workspace(workspace)
    assert payload is not None
    session_id = payload.get("active_session_id")
    return session_id if isinstance(session_id, str) and session_id else None


def active_record(workspace: Path, data_root: Path | None = None) -> dict[str, Any]:
    session_id = active_session_id(workspace)
    if not session_id:
        raise WorkspaceError("No active session is checked out. Run `clfc checkout <session>` first.")
    try:
        return resolve_record(session_id, workspace=workspace, data_root=data_root)
    except ResolveError as error:
        raise WorkspaceError(f"Active session {session_id!r} is not in the index. Run `clfc index`.") from error


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
