from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from clfc.core.index import clfc_data_root, read_all_records, read_workspace_records
from clfc.core.runtime import runtime_root
from clfc.utils.hashing import workspace_hash


@dataclass
class GcCandidate:
    kind: str
    target: str
    reason: str
    path: Path

    def to_dict(self) -> dict[str, str]:
        return {
            "kind": self.kind,
            "target": self.target,
            "reason": self.reason,
            "path": str(self.path),
        }


@dataclass
class GcResult:
    candidates: list[GcCandidate]
    removed: list[GcCandidate]

    @property
    def removed_count(self) -> int:
        return len(self.removed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_count": len(self.candidates),
            "removed_count": len(self.removed),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "removed": [candidate.to_dict() for candidate in self.removed],
        }


def collect_gc_candidates(
    workspace: Path,
    *,
    all_workspaces: bool = False,
    data_root: Path | None = None,
    runtime_base: Path | None = None,
) -> list[GcCandidate]:
    data = (data_root or clfc_data_root()).expanduser().resolve()
    runtime = (runtime_base or runtime_root()).expanduser().resolve()
    records = read_all_records(data) if all_workspaces else read_workspace_records(workspace, data)
    valid_keys = {
        (str(record.get("workspace_hash") or ""), str(record.get("session_id") or ""))
        for record in records
        if record.get("workspace_hash") and record.get("session_id")
    }

    candidates: list[GcCandidate] = []
    for record in records:
        transcript_path = Path(str(record.get("path") or "")).expanduser()
        if not transcript_path.is_file():
            record_path = _record_path(data, record)
            candidates.append(
                GcCandidate(
                    kind="index",
                    target=str(record.get("session_id") or ""),
                    reason="transcript missing",
                    path=record_path,
                )
            )

    candidates.extend(_runtime_candidates(runtime, valid_keys, workspace=workspace, all_workspaces=all_workspaces))
    return candidates


def run_gc(
    workspace: Path,
    *,
    all_workspaces: bool = False,
    apply: bool = False,
    data_root: Path | None = None,
    runtime_base: Path | None = None,
) -> GcResult:
    data = (data_root or clfc_data_root()).expanduser().resolve()
    runtime = (runtime_base or runtime_root()).expanduser().resolve()
    candidates = collect_gc_candidates(
        workspace,
        all_workspaces=all_workspaces,
        data_root=data,
        runtime_base=runtime,
    )
    removed: list[GcCandidate] = []
    if apply:
        for candidate in candidates:
            if candidate.kind == "index":
                _remove_file(candidate.path, data)
            elif candidate.kind == "runtime":
                _remove_dir(candidate.path, runtime)
            removed.append(candidate)
    return GcResult(candidates=candidates, removed=removed)


def _runtime_candidates(
    runtime: Path,
    valid_keys: set[tuple[str, str]],
    *,
    workspace: Path,
    all_workspaces: bool,
) -> list[GcCandidate]:
    if not runtime.exists():
        return []
    allowed_hash = workspace_hash(workspace)
    candidates: list[GcCandidate] = []
    for workspace_dir in sorted(path for path in runtime.iterdir() if path.is_dir()):
        if not all_workspaces and workspace_dir.name != allowed_hash:
            continue
        for session_dir in sorted(path for path in workspace_dir.iterdir() if path.is_dir()):
            key = (workspace_dir.name, session_dir.name)
            if key not in valid_keys:
                candidates.append(
                    GcCandidate(
                        kind="runtime",
                        target=f"{workspace_dir.name}/{session_dir.name}",
                        reason="no indexed session",
                        path=session_dir,
                    )
                )
    return candidates


def _record_path(data_root: Path, record: dict[str, object]) -> Path:
    return (
        data_root
        / "workspaces"
        / str(record.get("workspace_hash") or "")
        / f"{str(record.get('session_id') or '')}.json"
    )


def _remove_file(path: Path, root: Path) -> None:
    path = path.expanduser().resolve()
    root = root.expanduser().resolve()
    if not _is_relative_to(path, root):
        raise ValueError(f"Refusing to remove file outside CLFC data root: {path}")
    if path.is_file():
        path.unlink()


def _remove_dir(path: Path, root: Path) -> None:
    path = path.expanduser().resolve()
    root = root.expanduser().resolve()
    if not _is_relative_to(path, root):
        raise ValueError(f"Refusing to remove directory outside CLFC runtime root: {path}")
    if path.is_dir():
        shutil.rmtree(path)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
