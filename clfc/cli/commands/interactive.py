from __future__ import annotations

import subprocess
from argparse import Namespace
from pathlib import Path

from clfc.core.runner import InteractiveOptions, build_interactive_command, run_interactive


def run(args: Namespace) -> int:
    options = InteractiveOptions(
        workspace=Path(args.workspace).expanduser().resolve() if args.workspace else Path.cwd(),
        model=args.model,
        effort=args.effort,
        permission_mode=args.permission_mode,
        dangerously_skip_permissions=args.dangerously_skip_permissions,
        allow_dangerously_skip_permissions=args.allow_dangerously_skip_permissions,
        resume=args.resume,
        continue_latest=args.continue_latest,
        name=args.name,
        bare=args.bare,
        add_dirs=args.add_dir or [],
        extra_args=_extra_args(args.extra_args or []),
    )
    command = build_interactive_command(options)
    if args.dry_run:
        print(subprocess.list2cmdline(command))
        return 0
    if "--dangerously-skip-permissions" in command:
        print("WARNING: launching Claude Code with permission checks bypassed.")
    return run_interactive(options)


def _extra_args(values: list[str]) -> list[str]:
    if values and values[0] == "--":
        return values[1:]
    return values
