from __future__ import annotations

import subprocess
from pathlib import Path

from clfc.core.runner import InteractiveOptions, build_interactive_command, run_interactive


def launch_record(
    record: dict[str, object],
    fallback_workspace: Path,
    *,
    model: str | None = None,
    effort: str | None = None,
    permission_mode: str | None = None,
    dangerously_skip_permissions: bool = False,
    allow_dangerously_skip_permissions: bool = False,
    fork_session: bool = False,
    name: str | None = None,
    bare: bool = False,
    add_dirs: list[str] | None = None,
    dry_run: bool = False,
) -> int:
    session_id = str(record.get("session_id") or "")
    record_cwd = Path(str(record.get("cwd") or fallback_workspace)).expanduser()
    launch_workspace = record_cwd.resolve() if record_cwd.exists() else fallback_workspace
    options = InteractiveOptions(
        workspace=launch_workspace,
        model=model,
        effort=effort,
        permission_mode=permission_mode,
        dangerously_skip_permissions=dangerously_skip_permissions,
        allow_dangerously_skip_permissions=allow_dangerously_skip_permissions,
        resume=session_id,
        fork_session=fork_session,
        name=name,
        bare=bare,
        add_dirs=add_dirs or [],
    )

    command = build_interactive_command(options)
    if dry_run:
        print(subprocess.list2cmdline(command))
        print(f"cwd: {launch_workspace}")
        return 0
    if "--dangerously-skip-permissions" in command:
        print("WARNING: launching Claude Code with permission checks bypassed.")
    return run_interactive(options)
