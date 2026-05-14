from __future__ import annotations

import subprocess
from pathlib import Path

from clfc.core.runtime import prepare_launch_workspace
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
    launch_workspace, real_workspace, _ = prepare_launch_workspace(record, fallback_workspace)
    combined_add_dirs = _combined_add_dirs(real_workspace, add_dirs or [])
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
        add_dirs=combined_add_dirs,
    )

    command = build_interactive_command(options)
    if dry_run:
        print(subprocess.list2cmdline(command))
        print(f"cwd: {launch_workspace}")
        return 0
    if "--dangerously-skip-permissions" in command:
        print("WARNING: launching Claude Code with permission checks bypassed.")
    return run_interactive(options)


def _combined_add_dirs(real_workspace: Path, add_dirs: list[str]) -> list[str]:
    real = str(real_workspace)
    normalized = {real.lower()}
    combined = [real]
    for value in add_dirs:
        if value.lower() not in normalized:
            combined.append(value)
            normalized.add(value.lower())
    return combined
