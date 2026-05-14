from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from clfc.core.runtime import (
    clear_memory,
    clone_memory,
    find_nearest_claude_md,
    init_memory,
    memory_status,
    prepare_launch_workspace,
    runtime_root,
    set_memory_mode,
    sync_memory,
)


class RuntimeTests(unittest.TestCase):
    def test_runtime_root_uses_env_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = runtime_root({"CLFC_RUNTIME_DIR": temp_dir})

        self.assertEqual(root, Path(temp_dir))

    def test_find_nearest_claude_md_walks_upward(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            nested = root / "a" / "b"
            nested.mkdir(parents=True)
            memory = root / "CLAUDE.md"
            memory.write_text("root memory", encoding="utf-8")

            found = find_nearest_claude_md(nested)

        self.assertEqual(found, memory)

    def test_sync_memory_copies_workspace_claude_md(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            workspace.mkdir()
            (workspace / "CLAUDE.md").write_text("project memory", encoding="utf-8")
            record = _record(workspace)

            payload = sync_memory(record, workspace, root=root / "runtime")
            status = memory_status(record, workspace, root=root / "runtime")

            self.assertEqual(Path(str(payload["memory_source_path"])).name, "CLAUDE.md")
            self.assertTrue(status["memory_exists"])
            self.assertEqual(Path(str(status["memory_path"])).read_text(encoding="utf-8"), "project memory")

    def test_manual_memory_init_clone_and_clear(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            workspace.mkdir()
            source = root / "source.md"
            source.write_text("manual memory", encoding="utf-8")
            record = _record(workspace)

            init_path = init_memory(record, workspace, root=root / "runtime")
            init_exists = init_path.exists()
            clone_path = clone_memory(record, workspace, source, root=root / "runtime")
            clone_text = clone_path.read_text(encoding="utf-8")
            status_after_clone = memory_status(record, workspace, root=root / "runtime")
            payload_after_clear = clear_memory(record, workspace, root=root / "runtime")
            status_after_clear = memory_status(record, workspace, root=root / "runtime")

            self.assertTrue(init_exists)
            self.assertEqual(clone_text, "manual memory")
            self.assertEqual(status_after_clone["memory_mode"], "manual")
            self.assertTrue(status_after_clone["memory_exists"])
            self.assertEqual(payload_after_clear["memory_mode"], "sync")
            self.assertFalse(status_after_clear["memory_exists"])

    def test_prepare_launch_workspace_syncs_and_returns_runtime_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            workspace.mkdir()
            (workspace / "CLAUDE.md").write_text("project memory", encoding="utf-8")
            record = _record(workspace)

            runtime_dir, real_workspace, payload = prepare_launch_workspace(record, workspace, root=root / "runtime")

            self.assertEqual(real_workspace, workspace)
            self.assertEqual(runtime_dir, Path(str(payload["runtime_workspace"])))
            self.assertTrue((runtime_dir / "CLAUDE.md").exists())

    def test_set_memory_mode_rejects_unknown_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir) / "workspace"
            workspace.mkdir()
            with self.assertRaises(ValueError):
                set_memory_mode(_record(workspace), workspace, "weird", root=Path(temp_dir) / "runtime")


def _record(workspace: Path) -> dict[str, object]:
    return {
        "session_id": "session-1",
        "workspace_hash": "abc123",
        "cwd": str(workspace),
    }


if __name__ == "__main__":
    unittest.main()
