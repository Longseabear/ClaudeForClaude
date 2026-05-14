from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from clfc.core.index import write_index
from clfc.core.paths import iter_transcript_files, workspace_transcripts
from clfc.core.transcript import summarize_transcript


def run(args: Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else Path.cwd()
    files = iter_transcript_files() if args.all else workspace_transcripts(workspace)
    summaries = [summarize_transcript(path) for path in files]
    result = write_index(summaries)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return 0

    scope = "all workspaces" if args.all else str(workspace)
    print(f"Indexed transcripts: {scope}")
    print(f"  data root: {result.data_root}")
    print(f"  indexed: {result.indexed_count}")
    print(f"  skipped: {result.skipped_count}")
    for skipped in result.skipped:
        print(f"  skipped {skipped['session_id']}: {skipped['reason']}")
    return 0
