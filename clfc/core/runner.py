from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from clfc.core.settings import load_settings


@dataclass
class InteractiveOptions:
    workspace: Path
    model: str | None = None
    effort: str | None = None
    permission_mode: str | None = None
    dangerously_skip_permissions: bool = False
    allow_dangerously_skip_permissions: bool = False
    resume: str | None = None
    fork_session: bool = False
    continue_latest: bool = False
    name: str | None = None
    bare: bool = False
    add_dirs: list[str] = field(default_factory=list)
    extra_args: list[str] = field(default_factory=list)
    print_response: bool = False
    prompt: str | None = None
    output_format: str | None = None
    input_format: str | None = None
    system_prompt: str | None = None
    append_system_prompt: str | None = None


def build_interactive_command(options: InteractiveOptions) -> list[str]:
    settings = load_settings()
    defaults = settings["defaults"]
    command = ["claude"]

    model = options.model or defaults.get("model")
    effort = options.effort or defaults.get("effort")
    permission_mode = options.permission_mode or defaults.get("permission_mode")
    dangerously_skip = bool(defaults.get("dangerously_skip_permissions")) or options.dangerously_skip_permissions
    allow_dangerously_skip = (
        bool(defaults.get("allow_dangerously_skip_permissions")) or options.allow_dangerously_skip_permissions
    )

    if model:
        command.extend(["--model", str(model)])
    if effort:
        command.extend(["--effort", str(effort)])
    if permission_mode:
        command.extend(["--permission-mode", str(permission_mode)])
    if allow_dangerously_skip:
        command.append("--allow-dangerously-skip-permissions")
    if dangerously_skip:
        command.append("--dangerously-skip-permissions")
    if options.system_prompt:
        command.extend(["--system-prompt", options.system_prompt])
    if options.append_system_prompt:
        command.extend(["--append-system-prompt", options.append_system_prompt])
    if options.resume:
        command.extend(["--resume", options.resume])
    if options.fork_session:
        command.append("--fork-session")
    if options.continue_latest:
        command.append("--continue")
    if options.name:
        command.extend(["--name", options.name])
    if options.bare:
        command.append("--bare")
    for add_dir in options.add_dirs:
        command.extend(["--add-dir", add_dir])
    if options.print_response:
        command.append("--print")
    if options.output_format:
        command.extend(["--output-format", options.output_format])
    if options.input_format:
        command.extend(["--input-format", options.input_format])
    command.extend(options.extra_args)
    if options.prompt is not None:
        command.append(options.prompt)
    return command


def run_interactive(options: InteractiveOptions) -> int:
    if shutil.which("claude") is None:
        raise FileNotFoundError("claude executable was not found on PATH.")
    return subprocess.run(build_interactive_command(options), cwd=options.workspace).returncode
