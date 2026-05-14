from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path

from clfc.cli.commands.launch import launch_record
from clfc.core.index import ResolveError, resolve_record, write_index
from clfc.core.paths import iter_transcript_files, workspace_transcripts
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

    return launch_record(
        record,
        workspace,
        model=args.model,
        effort=args.effort,
        permission_mode=args.permission_mode,
        dangerously_skip_permissions=args.dangerously_skip_permissions,
        allow_dangerously_skip_permissions=args.allow_dangerously_skip_permissions,
        fork_session=True,
        name=args.name,
        bare=args.bare,
        add_dirs=args.add_dir or [],
        dry_run=args.dry_run,
    )
