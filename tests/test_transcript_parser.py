from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from clfc.core.paths import workspace_transcripts
from clfc.core.transcript import summarize_transcript


class TranscriptParserTests(unittest.TestCase):
    def test_summarize_transcript_counts_safe_shapes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "project" / "session-1.jsonl"
            path.parent.mkdir()
            _write_jsonl(
                path,
                [
                    {"type": "queue-operation", "operation": "enqueue", "sessionId": "session-1", "content": "secret prompt"},
                    {"type": "queue-operation", "operation": "dequeue", "sessionId": "session-1"},
                    {
                        "type": "user",
                        "sessionId": "session-1",
                        "timestamp": "2026-01-01T00:00:00Z",
                        "cwd": str(Path(temp_dir)),
                        "uuid": "u1",
                        "message": {"role": "user", "content": "secret prompt"},
                    },
                    {
                        "type": "assistant",
                        "sessionId": "session-1",
                        "timestamp": "2026-01-01T00:00:01Z",
                        "cwd": str(Path(temp_dir)),
                        "uuid": "a1",
                        "parentUuid": "u1",
                        "message": {
                            "id": "msg-1",
                            "role": "assistant",
                            "model": "gpt-oss:20b",
                            "content": [{"type": "thinking", "thinking": "hidden"}],
                            "usage": {"input_tokens": 10, "output_tokens": 4},
                        },
                    },
                    {
                        "type": "assistant",
                        "sessionId": "session-1",
                        "timestamp": "2026-01-01T00:00:01Z",
                        "cwd": str(Path(temp_dir)),
                        "uuid": "a2",
                        "parentUuid": "a1",
                        "message": {
                            "id": "msg-1",
                            "role": "assistant",
                            "model": "gpt-oss:20b",
                            "content": [{"type": "text", "text": "hidden"}],
                            "usage": {"input_tokens": 10, "output_tokens": 4},
                        },
                    },
                    {
                        "type": "assistant",
                        "sessionId": "session-1",
                        "timestamp": "2026-01-01T00:00:02Z",
                        "cwd": str(Path(temp_dir)),
                        "uuid": "a3",
                        "parentUuid": "a2",
                        "message": {
                            "id": "msg-2",
                            "role": "assistant",
                            "model": "gpt-oss:20b",
                            "content": [{"type": "tool_use", "id": "tool-1", "name": "Bash", "input": {"command": "secret"}}],
                            "usage": {"input_tokens": 12, "output_tokens": 6},
                        },
                    },
                    {
                        "type": "user",
                        "sessionId": "session-1",
                        "timestamp": "2026-01-01T00:00:03Z",
                        "cwd": str(Path(temp_dir)),
                        "uuid": "u2",
                        "parentUuid": "a3",
                        "message": {
                            "role": "user",
                            "content": [{"type": "tool_result", "tool_use_id": "tool-1", "content": "secret", "is_error": True}],
                        },
                    },
                    {"type": "last-prompt", "sessionId": "session-1", "leafUuid": "u2", "lastPrompt": "secret"},
                ],
            )

            summary = summarize_transcript(path, include_events=True)

        self.assertEqual(summary.session_id, "session-1")
        self.assertEqual(summary.record_counts["assistant"], 3)
        self.assertEqual(summary.role_counts["user"], 2)
        self.assertEqual(summary.block_counts["thinking"], 1)
        self.assertEqual(summary.block_counts["text"], 1)
        self.assertEqual(summary.tool_counts["Bash"], 1)
        self.assertEqual(summary.tool_error_count, 1)
        self.assertEqual(summary.usage.input_tokens, 22)
        self.assertEqual(summary.usage.output_tokens, 10)
        self.assertEqual(summary.leaf_uuid, "u2")
        self.assertEqual(summary.events[5].tool_names, ["Bash"])

    def test_workspace_transcripts_match_record_cwd_not_directory_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "workspace"
            workspace.mkdir()
            projects_root = Path(temp_dir) / "projects"
            transcript = projects_root / "encoded-name" / "session-2.jsonl"
            transcript.parent.mkdir(parents=True)
            _write_jsonl(
                transcript,
                [
                    {
                        "type": "user",
                        "sessionId": "session-2",
                        "cwd": str(workspace),
                        "message": {"role": "user", "content": "secret"},
                    }
                ],
            )

            matches = workspace_transcripts(workspace, projects_root)

        self.assertEqual(matches, [transcript])


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text("\n".join(json.dumps(record) for record in records), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
