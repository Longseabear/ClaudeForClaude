from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from clfc.cli.commands import open as open_command
from clfc.core.index import resolve_record, write_index
from clfc.core.transcript import summarize_transcript
from clfc.core.workspace import active_session_id


class OpenCommandTests(unittest.TestCase):
    def test_open_checkout_selects_numbered_session(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            workspace.mkdir()
            data_root = root / "data"
            transcripts = [
                _transcript(root, workspace, "old-session", "2026-01-01T00:00:00Z"),
                _transcript(root, workspace, "new-session", "2026-01-02T00:00:00Z"),
            ]
            write_index([summarize_transcript(path) for path in transcripts], data_root=data_root)

            with patch.dict(os.environ, {"CLFC_DATA_DIR": str(data_root)}):
                with redirect_stdout(io.StringIO()):
                    status = open_command.run(_args(workspace, select=1, action="checkout"))
                active = active_session_id(workspace)

        self.assertEqual(status, 0)
        self.assertEqual(active, "new-session")

    def test_open_name_action_sets_display_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            workspace.mkdir()
            data_root = root / "data"
            transcript = _transcript(root, workspace, "session-1", "2026-01-01T00:00:00Z")
            write_index([summarize_transcript(transcript)], data_root=data_root)

            with patch.dict(os.environ, {"CLFC_DATA_DIR": str(data_root)}):
                with redirect_stdout(io.StringIO()):
                    status = open_command.run(_args(workspace, select=1, action="name", display_name="main"))
                record = resolve_record("main", workspace, data_root=data_root)

        self.assertEqual(status, 0)
        self.assertEqual(record["session_id"], "session-1")
        self.assertEqual(record["display_name"], "main")

    def test_open_rejects_invalid_scripted_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            workspace.mkdir()
            data_root = root / "data"
            transcript = _transcript(root, workspace, "session-1", "2026-01-01T00:00:00Z")
            write_index([summarize_transcript(transcript)], data_root=data_root)

            stderr = io.StringIO()
            with patch.dict(os.environ, {"CLFC_DATA_DIR": str(data_root)}):
                with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
                    status = open_command.run(_args(workspace, select=2, action="checkout"))

        self.assertEqual(status, 2)
        self.assertIn("--select must be between 1 and 1", stderr.getvalue())


def _args(workspace: Path, **overrides: object) -> Namespace:
    payload: dict[str, object] = {
        "workspace": str(workspace),
        "all": False,
        "refresh": False,
        "limit": 20,
        "select": None,
        "action": None,
        "display_name": None,
        "launch_name": None,
        "model": None,
        "effort": None,
        "permission_mode": None,
        "dangerously_skip_permissions": False,
        "allow_dangerously_skip_permissions": False,
        "bare": False,
        "add_dir": None,
        "dry_run": False,
    }
    payload.update(overrides)
    return Namespace(**payload)


def _transcript(root: Path, workspace: Path, session_id: str, timestamp: str) -> Path:
    transcript = root / "projects" / "encoded" / f"{session_id}.jsonl"
    transcript.parent.mkdir(parents=True, exist_ok=True)
    transcript.write_text(
        json.dumps(
            {
                "type": "user",
                "sessionId": session_id,
                "timestamp": timestamp,
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
