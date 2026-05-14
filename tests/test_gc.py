from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from clfc.core.gc import collect_gc_candidates, run_gc
from clfc.core.index import write_index
from clfc.core.transcript import summarize_transcript


class GcTests(unittest.TestCase):
    def test_collects_missing_transcript_index_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            workspace.mkdir()
            data_root = root / "data"
            transcript = _transcript(root, workspace, "session-1")
            write_index([summarize_transcript(transcript)], data_root=data_root)
            transcript.unlink()

            candidates = collect_gc_candidates(workspace, data_root=data_root, runtime_base=root / "runtime")

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].kind, "index")
        self.assertEqual(candidates[0].target, "session-1")

    def test_apply_removes_stale_index_and_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            workspace.mkdir()
            data_root = root / "data"
            runtime_root = root / "runtime"
            transcript = _transcript(root, workspace, "session-1")
            result = write_index([summarize_transcript(transcript)], data_root=data_root)
            record = result.indexed[0]
            transcript.unlink()
            runtime_dir = runtime_root / str(record["workspace_hash"]) / "missing-session"
            runtime_dir.mkdir(parents=True)

            gc_result = run_gc(workspace, apply=True, data_root=data_root, runtime_base=runtime_root)

        self.assertEqual(gc_result.removed_count, 2)
        self.assertFalse(gc_result.removed[0].path.exists())
        self.assertFalse(runtime_dir.exists())


def _transcript(root: Path, workspace: Path, session_id: str) -> Path:
    transcript = root / "projects" / "encoded" / f"{session_id}.jsonl"
    transcript.parent.mkdir(parents=True, exist_ok=True)
    transcript.write_text(
        json.dumps(
            {
                "type": "user",
                "sessionId": session_id,
                "timestamp": "2026-01-01T00:00:00Z",
                "cwd": str(workspace),
                "message": {"role": "user", "content": "secret"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return transcript


if __name__ == "__main__":
    unittest.main()
