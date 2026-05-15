from __future__ import annotations

import io
import os
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from clfc.cli.commands import add as add_command
from clfc.core.index import resolve_record
from clfc.core.workspace import active_session_id


class AddCommandTests(unittest.TestCase):
    def test_add_creates_and_checkouts_named_session(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace"
            workspace.mkdir()
            data_root = root / "data"

            with patch.dict(os.environ, {"CLFC_DATA_DIR": str(data_root)}):
                with redirect_stdout(io.StringIO()):
                    status = add_command.run(_args(workspace, display_name="builder", checkout=True))
                record = resolve_record("builder", workspace, data_root=data_root)
                active = active_session_id(workspace)

        self.assertEqual(status, 0)
        self.assertEqual(record["launch_mode"], "session-id")
        self.assertEqual(active, record["session_id"])


def _args(workspace: Path, **overrides: object) -> Namespace:
    payload: dict[str, object] = {
        "display_name": "builder",
        "session": None,
        "workspace": str(workspace),
        "all": False,
        "refresh": False,
        "checkout": False,
        "json": False,
    }
    payload.update(overrides)
    return Namespace(**payload)


if __name__ == "__main__":
    unittest.main()
