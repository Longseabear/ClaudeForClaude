from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RUNTIME_SCHEMA_VERSION = 1
MEMORY_MODES = {"sync", "manual"}
PROMPT_MODES = {"off", "append", "replace"}


class RuntimeError(ValueError):
    pass


def runtime_root(env: dict[str, str] | None = None) -> Path:
    env = env or os.environ
    configured = env.get("CLFC_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".clfc"


def session_runtime_dir(record: dict[str, Any], fallback_workspace: Path, root: Path | None = None) -> Path:
    workspace_hash = str(record.get("workspace_hash") or "")
    session_id = str(record.get("session_id") or "")
    if not workspace_hash or not session_id:
        raise RuntimeError("Indexed records require workspace_hash and session_id.")
    return (root or runtime_root()).expanduser().resolve() / workspace_hash / session_id


def session_json_path(record: dict[str, Any], fallback_workspace: Path, root: Path | None = None) -> Path:
    return session_runtime_dir(record, fallback_workspace, root) / "session.json"


def ensure_session_runtime(record: dict[str, Any], fallback_workspace: Path, root: Path | None = None) -> dict[str, Any]:
    runtime_dir = session_runtime_dir(record, fallback_workspace, root)
    path = runtime_dir / "session.json"
    existing = _load_json(path)
    now = _now()
    real_workspace = _real_workspace(record, fallback_workspace)
    payload = existing or {}
    payload.update(
        {
            "schema_version": RUNTIME_SCHEMA_VERSION,
            "session_id": str(record.get("session_id") or ""),
            "workspace_hash": str(record.get("workspace_hash") or ""),
            "real_workspace": str(real_workspace),
            "runtime_workspace": str(runtime_dir),
            "display_name": record.get("display_name"),
            "updated_at": now,
        }
    )
    payload.setdefault("created_at", now)
    payload.setdefault("memory_mode", "sync")
    payload.setdefault("prompt_mode", "off")
    runtime_dir.mkdir(parents=True, exist_ok=True)
    _write_json(path, payload)
    return payload


def load_session_runtime(record: dict[str, Any], fallback_workspace: Path, root: Path | None = None) -> dict[str, Any]:
    return ensure_session_runtime(record, fallback_workspace, root)


def prepare_launch_workspace(
    record: dict[str, Any],
    fallback_workspace: Path,
    root: Path | None = None,
) -> tuple[Path, Path, dict[str, Any]]:
    payload = ensure_session_runtime(record, fallback_workspace, root)
    real_workspace = Path(str(payload["real_workspace"])).expanduser().resolve()
    runtime_dir = Path(str(payload["runtime_workspace"])).expanduser().resolve()
    if payload.get("memory_mode") == "sync":
        sync_memory(record, fallback_workspace, root)
    return runtime_dir, real_workspace, load_session_runtime(record, fallback_workspace, root)


def set_memory_mode(
    record: dict[str, Any],
    fallback_workspace: Path,
    mode: str,
    root: Path | None = None,
) -> dict[str, Any]:
    if mode not in MEMORY_MODES:
        raise RuntimeError(f"Unknown memory mode {mode!r}. Allowed: {', '.join(sorted(MEMORY_MODES))}")
    payload = ensure_session_runtime(record, fallback_workspace, root)
    payload["memory_mode"] = mode
    if mode == "manual":
        payload.pop("memory_source_path", None)
        payload.pop("memory_synced_at", None)
    payload["updated_at"] = _now()
    _write_json(Path(str(payload["runtime_workspace"])) / "session.json", payload)
    return payload


def init_memory(record: dict[str, Any], fallback_workspace: Path, root: Path | None = None) -> Path:
    payload = set_memory_mode(record, fallback_workspace, "manual", root)
    path = Path(str(payload["runtime_workspace"])) / "CLAUDE.md"
    if not path.exists():
        path.write_text(
            "# CLAUDE.md\n\nSession-local memory for this ClaudeForClaude session.\n",
            encoding="utf-8",
        )
    return path


def clone_memory(record: dict[str, Any], fallback_workspace: Path, source: Path, root: Path | None = None) -> Path:
    source = source.expanduser().resolve()
    if not source.is_file():
        raise RuntimeError(f"Memory source is not a file: {source}")
    payload = set_memory_mode(record, fallback_workspace, "manual", root)
    target = Path(str(payload["runtime_workspace"])) / "CLAUDE.md"
    shutil.copyfile(source, target)
    return target


def clear_memory(record: dict[str, Any], fallback_workspace: Path, root: Path | None = None) -> dict[str, Any]:
    payload = set_memory_mode(record, fallback_workspace, "sync", root)
    memory_path = Path(str(payload["runtime_workspace"])) / "CLAUDE.md"
    if memory_path.exists():
        memory_path.unlink()
    payload.pop("memory_source_path", None)
    payload.pop("memory_synced_at", None)
    _write_json(Path(str(payload["runtime_workspace"])) / "session.json", payload)
    return payload


def sync_memory(record: dict[str, Any], fallback_workspace: Path, root: Path | None = None) -> dict[str, Any]:
    payload = ensure_session_runtime(record, fallback_workspace, root)
    real_workspace = Path(str(payload["real_workspace"])).expanduser().resolve()
    source = find_nearest_claude_md(real_workspace)
    if source is None:
        return payload
    target = Path(str(payload["runtime_workspace"])) / "CLAUDE.md"
    shutil.copyfile(source, target)
    payload["memory_source_path"] = str(source)
    payload["memory_synced_at"] = _now()
    _write_json(Path(str(payload["runtime_workspace"])) / "session.json", payload)
    return payload


def memory_status(record: dict[str, Any], fallback_workspace: Path, root: Path | None = None) -> dict[str, Any]:
    payload = ensure_session_runtime(record, fallback_workspace, root)
    memory_path = Path(str(payload["runtime_workspace"])) / "CLAUDE.md"
    payload["memory_path"] = str(memory_path)
    payload["memory_exists"] = memory_path.exists()
    return payload


def set_prompt_mode(
    record: dict[str, Any],
    fallback_workspace: Path,
    mode: str,
    root: Path | None = None,
) -> dict[str, Any]:
    if mode not in PROMPT_MODES:
        raise RuntimeError(f"Unknown prompt mode {mode!r}. Allowed: {', '.join(sorted(PROMPT_MODES))}")
    payload = ensure_session_runtime(record, fallback_workspace, root)
    payload["prompt_mode"] = mode
    payload["updated_at"] = _now()
    _write_json(Path(str(payload["runtime_workspace"])) / "session.json", payload)
    return payload


def init_prompt(record: dict[str, Any], fallback_workspace: Path, root: Path | None = None) -> Path:
    payload = set_prompt_mode(record, fallback_workspace, "append", root)
    path = Path(str(payload["runtime_workspace"])) / "system_prompt.md"
    if not path.exists():
        path.write_text(
            "# System prompt overlay\n\nAdd session-specific system prompt instructions here.\n",
            encoding="utf-8",
        )
    return path


def clone_prompt(record: dict[str, Any], fallback_workspace: Path, source: Path, root: Path | None = None) -> Path:
    source = source.expanduser().resolve()
    if not source.is_file():
        raise RuntimeError(f"Prompt source is not a file: {source}")
    payload = set_prompt_mode(record, fallback_workspace, "append", root)
    target = Path(str(payload["runtime_workspace"])) / "system_prompt.md"
    shutil.copyfile(source, target)
    return target


def save_prompt_text(
    record: dict[str, Any],
    fallback_workspace: Path,
    text: str,
    *,
    mode: str = "append",
    root: Path | None = None,
) -> Path:
    payload = set_prompt_mode(record, fallback_workspace, mode, root)
    target = Path(str(payload["runtime_workspace"])) / "system_prompt.md"
    target.write_text(text, encoding="utf-8")
    payload["prompt_rendered_at"] = _now()
    _write_json(Path(str(payload["runtime_workspace"])) / "session.json", payload)
    return target


def clear_prompt(record: dict[str, Any], fallback_workspace: Path, root: Path | None = None) -> dict[str, Any]:
    payload = set_prompt_mode(record, fallback_workspace, "off", root)
    prompt_path = Path(str(payload["runtime_workspace"])) / "system_prompt.md"
    if prompt_path.exists():
        prompt_path.unlink()
    payload.pop("prompt_rendered_at", None)
    _write_json(Path(str(payload["runtime_workspace"])) / "session.json", payload)
    return payload


def prompt_status(record: dict[str, Any], fallback_workspace: Path, root: Path | None = None) -> dict[str, Any]:
    payload = ensure_session_runtime(record, fallback_workspace, root)
    prompt_path = Path(str(payload["runtime_workspace"])) / "system_prompt.md"
    payload["prompt_path"] = str(prompt_path)
    payload["prompt_exists"] = prompt_path.exists()
    return payload


def prompt_overrides(
    record: dict[str, Any],
    fallback_workspace: Path,
    root: Path | None = None,
) -> tuple[str | None, str | None]:
    payload = ensure_session_runtime(record, fallback_workspace, root)
    mode = str(payload.get("prompt_mode") or "off")
    prompt_path = Path(str(payload["runtime_workspace"])) / "system_prompt.md"
    if mode == "off" or not prompt_path.is_file():
        return None, None
    text = prompt_path.read_text(encoding="utf-8-sig")
    if not text.strip():
        return None, None
    if mode == "replace":
        return text, None
    if mode == "append":
        return None, text
    return None, None


def find_nearest_claude_md(start: Path) -> Path | None:
    current = start.expanduser().resolve()
    if current.is_file():
        current = current.parent
    for parent in [current, *current.parents]:
        candidate = parent / "CLAUDE.md"
        if candidate.is_file():
            return candidate
    return None


def _real_workspace(record: dict[str, Any], fallback_workspace: Path) -> Path:
    raw = record.get("cwd")
    if isinstance(raw, str) and raw:
        candidate = Path(raw).expanduser()
        if candidate.exists():
            return candidate.resolve()
    return fallback_workspace.expanduser().resolve()


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
