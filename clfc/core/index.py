from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from clfc.core.summaries import TranscriptSummary
from clfc.utils.hashing import workspace_hash

SCHEMA_VERSION = 1


@dataclass
class IndexResult:
    data_root: Path
    indexed: list[dict[str, Any]]
    skipped: list[dict[str, str]]

    @property
    def indexed_count(self) -> int:
        return len(self.indexed)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped)

    def to_dict(self) -> dict[str, Any]:
        return {
            "data_root": str(self.data_root),
            "indexed_count": self.indexed_count,
            "skipped_count": self.skipped_count,
            "indexed": self.indexed,
            "skipped": self.skipped,
        }


class ResolveError(ValueError):
    pass


def clfc_data_root(env: dict[str, str] | None = None) -> Path:
    env = env or os.environ
    configured = env.get("CLFC_DATA_DIR")
    if configured:
        return Path(configured).expanduser()
    local_app_data = env.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "clfc"
    return Path.home() / ".clfc"


def write_index(summaries: list[TranscriptSummary], data_root: Path | None = None) -> IndexResult:
    root = (data_root or clfc_data_root()).expanduser().resolve()
    indexed: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    indexed_at = _now()

    for summary in summaries:
        if not summary.cwd:
            skipped.append({"session_id": summary.session_id, "reason": "missing cwd"})
            continue
        record = summary_to_record(summary, indexed_at=indexed_at)
        workspace_dir = root / "workspaces" / record["workspace_hash"]
        workspace_dir.mkdir(parents=True, exist_ok=True)
        _write_json(workspace_dir / f"{summary.session_id}.json", record)
        indexed.append(record)

    root.mkdir(parents=True, exist_ok=True)
    _write_json(
        root / "state.json",
        {
            "schema_version": SCHEMA_VERSION,
            "last_indexed_at": indexed_at,
            "last_indexed_count": len(indexed),
            "last_skipped_count": len(skipped),
        },
    )
    return IndexResult(data_root=root, indexed=indexed, skipped=skipped)


def summary_to_record(summary: TranscriptSummary, indexed_at: str | None = None) -> dict[str, Any]:
    if not summary.cwd:
        raise ValueError("Cannot index a transcript summary without cwd.")
    payload = summary.to_dict(include_events=False)
    payload.update(
        {
            "schema_version": SCHEMA_VERSION,
            "workspace_hash": workspace_hash(Path(summary.cwd)),
            "indexed_at": indexed_at or _now(),
        }
    )
    return payload


def read_workspace_records(workspace: Path, data_root: Path | None = None) -> list[dict[str, Any]]:
    root = (data_root or clfc_data_root()).expanduser().resolve()
    workspace_dir = root / "workspaces" / workspace_hash(workspace)
    return sorted(_read_records(workspace_dir), key=lambda record: record.get("updated_at") or "", reverse=True)


def read_all_records(data_root: Path | None = None) -> list[dict[str, Any]]:
    root = (data_root or clfc_data_root()).expanduser().resolve()
    workspaces_dir = root / "workspaces"
    records: list[dict[str, Any]] = []
    if not workspaces_dir.exists():
        return []
    for workspace_dir in sorted(path for path in workspaces_dir.iterdir() if path.is_dir()):
        records.extend(_read_records(workspace_dir))
    return sorted(records, key=lambda record: record.get("updated_at") or "", reverse=True)


def resolve_record(
    session: str,
    workspace: Path,
    all_workspaces: bool = False,
    data_root: Path | None = None,
) -> dict[str, Any]:
    records = read_all_records(data_root) if all_workspaces else read_workspace_records(workspace, data_root)
    matches = [
        record
        for record in records
        if _matches_session(session, record)
    ]
    if not matches:
        scope = "all indexed workspaces" if all_workspaces else str(workspace)
        raise ResolveError(f"No indexed session matched {session!r} in {scope}. Run `clfc index` or use `--refresh`.")
    if len(matches) > 1:
        candidates = ", ".join(str(record.get("session_id", "")) for record in matches[:10])
        raise ResolveError(f"Ambiguous session prefix {session!r}; matched {len(matches)} sessions: {candidates}")
    return matches[0]


def _matches_session(session: str, record: dict[str, Any]) -> bool:
    session_id = str(record.get("session_id") or "")
    return session_id == session or session_id.startswith(session)


def _read_records(workspace_dir: Path) -> list[dict[str, Any]]:
    if not workspace_dir.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(workspace_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            records.append(payload)
    return records


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
