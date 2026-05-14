from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from clfc.core.index import write_index
from clfc.core.transcript import summarize_transcript
from clfc.core.workspace import (
    WorkspaceError,
    active_record,
    active_session_id,
    clear_active_session,
    init_workspace,
    load_workspace,
    set_active_session,
    workspace_json_path,
)


class WorkspaceTests(unittest.TestCase):
    def test_init_workspace_creates_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            payload = init_workspace(workspace)
            loaded = load_workspace(workspace)

        self.assertEqual(payload["workspace_path"], str(workspace.resolve()))
        self.assertEqual(loaded["workspace_hash"], payload["workspace_hash"])
        self.assertIsNone(loaded["active_session_id"])

    def test_set_and_clear_active_session(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            record = {
                "session_id": "session-1",
                "display_name": "main",
                "updated_at": "2026-01-01T00:00:00Z",
            }

            set_active_session(workspace, record)
            active = active_session_id(workspace)
            cleared = clear_active_session(workspace)

        self.assertEqual(active, "session-1")
        self.assertIsNone(cleared["active_session_id"])

    def test_init_preserves_active_session(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            set_active_session(workspace, {"session_id": "session-1"})

            payload = init_workspace(workspace)

        self.assertEqual(payload["active_session_id"], "session-1")

    def test_active_record_resolves_indexed_session(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            workspace.mkdir()
            transcript = root / "projects" / "encoded" / "session-1.jsonl"
            transcript.parent.mkdir(parents=True)
            transcript.write_text(
                '{"type":"user","sessionId":"session-1","cwd":"'
                + str(workspace).replace("\\", "\\\\")
                + '","message":{"role":"user","content":"secret"}}\n',
                encoding="utf-8",
            )
            data_root = root / "data"
            write_index([summarize_transcript(transcript)], data_root=data_root)
            set_active_session(workspace, {"session_id": "session-1"})

            record = active_record(workspace, data_root=data_root)

        self.assertEqual(record["session_id"], "session-1")

    def test_load_workspace_requires_init(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(WorkspaceError):
                load_workspace(Path(temp_dir))

    def test_active_record_requires_indexed_session(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            set_active_session(workspace, {"session_id": "missing-session"})

            with self.assertRaises(WorkspaceError):
                active_record(workspace, data_root=workspace / "missing-data")

    def test_workspace_json_path_is_local(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = workspace_json_path(Path(temp_dir))

        self.assertEqual(path.name, "workspace.json")
        self.assertEqual(path.parent.name, ".clfc")


if __name__ == "__main__":
    unittest.main()
