from __future__ import annotations

import subprocess
import sys
from argparse import Namespace
from pathlib import Path

from clfc.core.index import ResolveError, resolve_record, write_index
from clfc.core.paths import iter_transcript_files, workspace_transcripts
from clfc.core.runner import InteractiveOptions, build_interactive_command, run_interactive
from clfc.core.transcript import summarize_transcript
from clfc.core.workspace import WorkspaceError, active_record


def run(args: Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else Path.cwd()
    if args.refresh:
        files = iter_transcript_files() if args.all else workspace_transcripts(workspace)
        write_index([summarize_transcript(path) for path in files])

    try:
        record = (
            resolve_record(args.session, workspace=workspace, all_workspaces=args.all)
            if args.session
            else active_record(workspace)
        )
    except (ResolveError, WorkspaceError) as error:
        print(str(error), file=sys.stderr)
        return 1

    session_id = str(record.get("session_id") or "")
    record_cwd = Path(str(record.get("cwd") or workspace)).expanduser()
    launch_workspace = record_cwd.resolve() if record_cwd.exists() else workspace
    options = InteractiveOptions(
        workspace=launch_workspace,
        model=args.model,
        effort=args.effort,
        permission_mode=args.permission_mode,
        dangerously_skip_permissions=args.dangerously_skip_permissions,
        allow_dangerously_skip_permissions=args.allow_dangerously_skip_permissions,
        resume=session_id,
        fork_session=args.fork,
        name=args.name,
        bare=args.bare,
        add_dirs=args.add_dir or [],
    )

    command = build_interactive_command(options)
    if args.dry_run:
        print(subprocess.list2cmdline(command))
        print(f"cwd: {launch_workspace}")
        return 0
    if "--dangerously-skip-permissions" in command:
        print("WARNING: launching Claude Code with permission checks bypassed.")
    return run_interactive(options)
