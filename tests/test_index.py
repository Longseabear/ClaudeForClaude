from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from clfc.core.index import ResolveError, read_workspace_records, resolve_record, set_display_name, write_index
from clfc.core.transcript import summarize_transcript


class IndexTests(unittest.TestCase):
    def test_write_index_persists_safe_summary_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            workspace.mkdir()
            transcript = root / "projects" / "encoded" / "session-1.jsonl"
            transcript.parent.mkdir(parents=True)
            _write_jsonl(
                transcript,
                [
                    {
                        "type": "user",
                        "sessionId": "session-1",
                        "timestamp": "2026-01-01T00:00:00Z",
                        "cwd": str(workspace),
                        "message": {"role": "user", "content": "secret prompt text"},
                    },
                    {
                        "type": "assistant",
                        "sessionId": "session-1",
                        "timestamp": "2026-01-01T00:00:01Z",
                        "cwd": str(workspace),
                        "message": {
                            "id": "msg-1",
                            "role": "assistant",
                            "model": "gpt-oss:20b",
                            "content": [
                                {"type": "tool_use", "id": "tool-1", "name": "Bash", "input": {"command": "secret command"}}
                            ],
                            "usage": {"input_tokens": 5, "output_tokens": 3},
                        },
                    },
                    {
                        "type": "user",
                        "sessionId": "session-1",
                        "timestamp": "2026-01-01T00:00:02Z",
                        "cwd": str(workspace),
                        "message": {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": "tool-1",
                                    "content": "secret output",
                                    "is_error": False,
                                }
                            ],
                        },
                    },
                ],
            )
            summary = summarize_transcript(transcript)
            data_root = root / "clfc-data"

            result = write_index([summary], data_root=data_root)
            records = read_workspace_records(workspace, data_root=data_root)
            serialized = json.dumps(records, ensure_ascii=False)

        self.assertEqual(result.indexed_count, 1)
        self.assertEqual(len(records), 1)
        self.assertIn("Bash", serialized)
        self.assertIn("gpt-oss:20b", serialized)
        self.assertNotIn("secret prompt text", serialized)
        self.assertNotIn("secret command", serialized)
        self.assertNotIn("secret output", serialized)
        self.assertEqual(records[0]["usage"]["input_tokens"], 5)
        self.assertEqual(records[0]["tool_counts"]["Bash"], 1)

    def test_resolve_record_by_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            workspace.mkdir()
            transcript = root / "projects" / "encoded" / "abcdef12-0000-4000-8000-000000000000.jsonl"
            transcript.parent.mkdir(parents=True)
            _write_jsonl(
                transcript,
                [
                    {
                        "type": "user",
                        "sessionId": "abcdef12-0000-4000-8000-000000000000",
                        "timestamp": "2026-01-01T00:00:00Z",
                        "cwd": str(workspace),
                        "message": {"role": "user", "content": "secret"},
                    }
                ],
            )
            write_index([summarize_transcript(transcript)], data_root=root / "clfc-data")

            record = resolve_record("abcdef12", workspace, data_root=root / "clfc-data")

        self.assertEqual(record["session_id"], "abcdef12-0000-4000-8000-000000000000")

    def test_resolve_record_reports_ambiguous_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            workspace.mkdir()
            transcripts = []
            for session_id in [
                "abcdef12-0000-4000-8000-000000000000",
                "abcdef99-0000-4000-8000-000000000000",
            ]:
                transcript = root / "projects" / "encoded" / f"{session_id}.jsonl"
                transcript.parent.mkdir(parents=True, exist_ok=True)
                _write_jsonl(
                    transcript,
                    [
                        {
                            "type": "user",
                            "sessionId": session_id,
                            "timestamp": "2026-01-01T00:00:00Z",
                            "cwd": str(workspace),
                            "message": {"role": "user", "content": "secret"},
                        }
                    ],
                )
                transcripts.append(transcript)
            write_index([summarize_transcript(path) for path in transcripts], data_root=root / "clfc-data")

            with self.assertRaises(ResolveError):
                resolve_record("abcdef", workspace, data_root=root / "clfc-data")

    def test_display_name_resolves_and_survives_reindex(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            workspace.mkdir()
            transcript = root / "projects" / "encoded" / "abcdef12-0000-4000-8000-000000000000.jsonl"
            transcript.parent.mkdir(parents=True)
            _write_jsonl(
                transcript,
                [
                    {
                        "type": "user",
                        "sessionId": "abcdef12-0000-4000-8000-000000000000",
                        "timestamp": "2026-01-01T00:00:00Z",
                        "cwd": str(workspace),
                        "message": {"role": "user", "content": "secret"},
                    }
                ],
            )
            data_root = root / "clfc-data"
            summary = summarize_transcript(transcript)
            write_index([summary], data_root=data_root)
            set_display_name("abcdef12", "main", workspace, data_root=data_root)
            write_index([summary], data_root=data_root)

            record = resolve_record("main", workspace, data_root=data_root)

        self.assertEqual(record["session_id"], "abcdef12-0000-4000-8000-000000000000")
        self.assertEqual(record["display_name"], "main")

    def test_duplicate_display_name_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            workspace.mkdir()
            transcripts = []
            for session_id in [
                "aaaaaa12-0000-4000-8000-000000000000",
                "bbbbbb12-0000-4000-8000-000000000000",
            ]:
                transcript = root / "projects" / "encoded" / f"{session_id}.jsonl"
                transcript.parent.mkdir(parents=True, exist_ok=True)
                _write_jsonl(
                    transcript,
                    [
                        {
                            "type": "user",
                            "sessionId": session_id,
                            "timestamp": "2026-01-01T00:00:00Z",
                            "cwd": str(workspace),
                            "message": {"role": "user", "content": "secret"},
                        }
                    ],
                )
                transcripts.append(transcript)
            data_root = root / "clfc-data"
            write_index([summarize_transcript(path) for path in transcripts], data_root=data_root)
            set_display_name("aaaaaa12", "main", workspace, data_root=data_root)

            with self.assertRaises(ResolveError):
                set_display_name("bbbbbb12", "main", workspace, data_root=data_root)


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
