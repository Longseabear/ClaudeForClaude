from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from clfc.core.index import ResolveError, resolve_record, write_index
from clfc.core.paths import iter_transcript_files, workspace_transcripts
from clfc.core.runtime import RuntimeError, clear_memory, clone_memory, init_memory, memory_status, set_memory_mode
from clfc.core.transcript import summarize_transcript
from clfc.core.workspace import WorkspaceError, active_record


def run(args: Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else Path.cwd()
    if getattr(args, "refresh", False):
        files = iter_transcript_files() if args.all else workspace_transcripts(workspace)
        write_index([summarize_transcript(path) for path in files])

    try:
        record = _resolve_target(args, workspace)
        payload = _apply(args, record, workspace)
    except (ResolveError, WorkspaceError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    _print_human(args, payload)
    return 0


def _resolve_target(args: Namespace, workspace: Path) -> dict[str, object]:
    session = getattr(args, "session", None)
    if session:
        return resolve_record(session, workspace=workspace, all_workspaces=args.all)
    return active_record(workspace)


def _apply(args: Namespace, record: dict[str, object], workspace: Path) -> dict[str, object]:
    command = args.memory_command
    if command == "status":
        return memory_status(record, workspace)
    if command == "init":
        path = init_memory(record, workspace)
        return memory_status(record, workspace) | {"memory_path": str(path)}
    if command == "clone":
        path = clone_memory(record, workspace, Path(args.source))
        return memory_status(record, workspace) | {"memory_path": str(path)}
    if command == "clear":
        payload = clear_memory(record, workspace)
        return memory_status(record, workspace) | payload
    if command == "mode":
        payload = set_memory_mode(record, workspace, args.mode)
        return memory_status(record, workspace) | payload
    raise RuntimeError(f"Unknown memory command: {command}")


def _print_human(args: Namespace, payload: dict[str, object]) -> None:
    command = args.memory_command
    if command == "init":
        print(f"Initialized session memory: {payload['memory_path']}")
    elif command == "clone":
        print(f"Cloned session memory: {payload['memory_path']}")
    elif command == "clear":
        print("Cleared session-local CLAUDE.md and switched memory mode to sync.")
    elif command == "mode":
        print(f"Set memory mode: {payload['memory_mode']}")
    else:
        print(f"Memory mode: {payload['memory_mode']}")
    print(f"  runtime_workspace: {payload['runtime_workspace']}")
    print(f"  memory_path: {payload['memory_path']}")
    print(f"  memory_exists: {payload['memory_exists']}")
    source = payload.get("memory_source_path")
    if source:
        print(f"  memory_source_path: {source}")
