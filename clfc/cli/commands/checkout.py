from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from clfc.core.index import ResolveError, resolve_record, write_index
from clfc.core.paths import iter_transcript_files, workspace_transcripts
from clfc.core.transcript import summarize_transcript
from clfc.core.workspace import WorkspaceError, clear_active_session, set_active_session


def run(args: Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else Path.cwd()
    if not args.clear and not args.session:
        print("Expected a session id, prefix, or display name. Use --clear to clear checkout.", file=sys.stderr)
        return 2

    if args.clear:
        try:
            payload = clear_active_session(workspace)
        except WorkspaceError as error:
            print(str(error), file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("Cleared active session.")
        return 0

    if args.refresh:
        files = iter_transcript_files() if args.all else workspace_transcripts(workspace)
        write_index([summarize_transcript(path) for path in files])

    try:
        record = resolve_record(args.session, workspace=workspace, all_workspaces=args.all)
    except ResolveError as error:
        print(str(error), file=sys.stderr)
        return 1

    payload = set_active_session(workspace, record)
    if args.json:
        print(json.dumps({"workspace": payload, "session": record}, indent=2, ensure_ascii=False))
        return 0
    name = record.get("display_name") or "<unnamed>"
    print(f"Checked out {record.get('session_id')} ({name})")
    print(f"  workspace: {workspace}")
    return 0
