from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from clfc.core.prompt import PromptError, render_template, render_template_file
from clfc.core.runtime import prompt_overrides, prompt_status, save_prompt_text


class PromptTests(unittest.TestCase):
    def test_render_template_replaces_dictionary_values(self) -> None:
        rendered = render_template("Review {target} for {focus}.", {"target": "runner.py", "focus": "security"})

        self.assertEqual(rendered, "Review runner.py for security.")

    def test_render_template_reports_missing_value(self) -> None:
        with self.assertRaises(PromptError):
            render_template("Review {target}.", {})

    def test_render_template_file_merges_json_and_vars(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            template = root / "template.md"
            values = root / "values.json"
            template.write_text("Target: {target}\nFocus: {focus}\nMeta: {meta}", encoding="utf-8")
            values.write_text(json.dumps({"target": "old", "meta": {"risk": "high"}}), encoding="utf-8")

            rendered = render_template_file(
                template,
                vars_json=[str(values)],
                var_entries=["target=new", "focus=tests"],
            )

        self.assertIn("Target: new", rendered)
        self.assertIn("Focus: tests", rendered)
        self.assertIn('"risk": "high"', rendered)

    def test_save_prompt_text_sets_append_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            workspace.mkdir()
            record = {"session_id": "session-1", "workspace_hash": "abc123", "cwd": str(workspace)}

            save_prompt_text(record, workspace, "Be concise.", mode="append", root=root / "runtime")
            status = prompt_status(record, workspace, root=root / "runtime")
            system_prompt, append_prompt = prompt_overrides(record, workspace, root=root / "runtime")

        self.assertEqual(status["prompt_mode"], "append")
        self.assertTrue(status["prompt_exists"])
        self.assertIsNone(system_prompt)
        self.assertEqual(append_prompt, "Be concise.")


if __name__ == "__main__":
    unittest.main()
