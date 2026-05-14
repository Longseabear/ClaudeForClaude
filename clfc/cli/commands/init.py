from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from clfc.core.workspace import init_workspace, workspace_json_path


def run(args: Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else Path.cwd()
    payload = init_workspace(workspace)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    print(f"Initialized CLFC workspace: {workspace_json_path(workspace)}")
    print(f"  workspace_hash: {payload['workspace_hash']}")
    active = payload.get("active_session_id") or "<none>"
    print(f"  active_session_id: {active}")
    return 0
