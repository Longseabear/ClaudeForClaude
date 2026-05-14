from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from clfc.core.gc import run_gc
from clfc.utils.output import format_table


def run(args: Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else Path.cwd()
    try:
        result = run_gc(workspace, all_workspaces=args.all, apply=args.apply)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return 0

    if not result.candidates:
        print("No stale CLFC index records or runtime workspaces found.")
        return 0

    rows = [[candidate.kind, candidate.target, candidate.reason, candidate.path] for candidate in result.candidates]
    print(format_table(["kind", "target", "reason", "path"], rows))
    if args.apply:
        print(f"Removed {len(result.removed)} stale item(s).")
    else:
        print("Dry run only. Re-run with --apply to remove these CLFC-owned files.")
    return 0
