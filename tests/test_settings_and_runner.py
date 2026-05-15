from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from clfc.core.runner import InteractiveOptions, build_interactive_command
from clfc.core.settings import load_settings, set_default


class SettingsAndRunnerTests(unittest.TestCase):
    def test_settings_set_dangerously_skip_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = set_default("dangerously-skip-permissions", "on", data_root=Path(temp_dir))
            loaded = load_settings(data_root=Path(temp_dir))

        self.assertTrue(settings["defaults"]["dangerously_skip_permissions"])
        self.assertTrue(loaded["defaults"]["dangerously_skip_permissions"])

    def test_build_interactive_command_uses_saved_defaults_and_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            set_default("model", "gpt-oss:20b-cloud", data_root=root)
            set_default("permission-mode", "bypassPermissions", data_root=root)
            set_default("dangerously-skip-permissions", "on", data_root=root)
            with patch.dict(os.environ, {"CLFC_DATA_DIR": str(root)}):
                command = build_interactive_command(
                    InteractiveOptions(
                        workspace=Path(temp_dir),
                        effort="high",
                        resume="session-123",
                        fork_session=True,
                        add_dirs=["C:\\work"],
                        extra_args=["--debug"],
                    )
                )

        self.assertEqual(command[0], "claude")
        self.assertIn("--model", command)
        self.assertIn("gpt-oss:20b-cloud", command)
        self.assertIn("--permission-mode", command)
        self.assertIn("bypassPermissions", command)
        self.assertIn("--dangerously-skip-permissions", command)
        self.assertIn("--effort", command)
        self.assertIn("high", command)
        self.assertIn("--resume", command)
        self.assertIn("session-123", command)
        self.assertIn("--fork-session", command)
        self.assertIn("--add-dir", command)
        self.assertIn("C:\\work", command)
        self.assertIn("--debug", command)

    def test_permission_mode_default_is_a_real_value(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = set_default("permission-mode", "default", data_root=Path(temp_dir))

        self.assertEqual(settings["defaults"]["permission_mode"], "default")

    def test_cli_override_can_enable_skip_without_saved_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"CLFC_DATA_DIR": temp_dir}):
                command = build_interactive_command(
                    InteractiveOptions(
                        workspace=Path(temp_dir),
                        dangerously_skip_permissions=True,
                    )
                )

        self.assertIn("--dangerously-skip-permissions", command)

    def test_build_print_command_supports_prompt_and_system_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"CLFC_DATA_DIR": temp_dir}):
                command = build_interactive_command(
                    InteractiveOptions(
                        workspace=Path(temp_dir),
                        resume="session-123",
                        print_response=True,
                        output_format="json",
                        append_system_prompt="Be brief.",
                        prompt="Summarize the repo.",
                    )
                )

        self.assertIn("--print", command)
        self.assertIn("--output-format", command)
        self.assertIn("json", command)
        self.assertIn("--append-system-prompt", command)
        self.assertEqual(command[-1], "Summarize the repo.")

    def test_build_command_supports_explicit_session_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"CLFC_DATA_DIR": temp_dir}):
                command = build_interactive_command(
                    InteractiveOptions(
                        workspace=Path(temp_dir),
                        session_id="00000000-0000-4000-8000-000000000000",
                    )
                )

        self.assertIn("--session-id", command)
        self.assertIn("00000000-0000-4000-8000-000000000000", command)
        self.assertNotIn("--resume", command)


if __name__ == "__main__":
    unittest.main()
