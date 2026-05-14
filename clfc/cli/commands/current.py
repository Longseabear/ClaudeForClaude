from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from clfc.core.workspace import WorkspaceError, active_record, load_workspace, workspace_json_path


def run(args: Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else Path.cwd()
    try:
        payload = load_workspace(workspace)
        assert payload is not None
        record = active_record(workspace)
    except WorkspaceError as error:
        print(str(error), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"workspace": payload, "session": record}, indent=2, ensure_ascii=False))
        return 0

    print(f"Workspace: {workspace_json_path(workspace)}")
    print(f"Active session: {record.get('session_id')}")
    print(f"Name: {record.get('display_name') or '<unnamed>'}")
    print(f"Updated: {record.get('updated_at') or '<unknown>'}")
    print(f"Model(s): {', '.join((record.get('model_counts') or {}).keys()) or '<none>'}")
    print(f"Transcript: {record.get('path')}")
    return 0
