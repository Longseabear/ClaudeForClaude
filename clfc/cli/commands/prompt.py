from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

from clfc.core.index import ResolveError, resolve_record, write_index
from clfc.core.paths import iter_transcript_files, workspace_transcripts
from clfc.core.prompt import PromptError, render_template_file
from clfc.core.runtime import (
    RuntimeError,
    clear_prompt,
    clone_prompt,
    init_prompt,
    prompt_status,
    save_prompt_text,
    set_prompt_mode,
)
from clfc.core.transcript import summarize_transcript
from clfc.core.workspace import WorkspaceError, active_record


def run(args: Namespace) -> int:
    command = args.prompt_command
    if command == "render":
        return _render(args)

    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else Path.cwd()
    if getattr(args, "refresh", False):
        files = iter_transcript_files() if args.all else workspace_transcripts(workspace)
        write_index([summarize_transcript(path) for path in files])

    try:
        record = _target_record(args, workspace)
        if command == "status":
            payload = prompt_status(record, workspace)
        elif command == "init":
            payload = {"prompt_path": str(init_prompt(record, workspace))}
        elif command == "clone":
            payload = {"prompt_path": str(clone_prompt(record, workspace, Path(args.source)))}
        elif command == "clear":
            payload = clear_prompt(record, workspace)
        elif command == "mode":
            payload = set_prompt_mode(record, workspace, args.mode)
        elif command == "apply":
            text = render_template_file(Path(args.template), var_entries=args.var or [], vars_json=args.vars_json or [])
            payload = {"prompt_path": str(save_prompt_text(record, workspace, text, mode=args.mode))}
        else:
            print("Expected a prompt subcommand.", file=sys.stderr)
            return 2
    except (ResolveError, RuntimeError, WorkspaceError, PromptError) as error:
        print(str(error), file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    _print_result(command, payload)
    return 0


def _render(args: Namespace) -> int:
    try:
        text = render_template_file(Path(args.template), var_entries=args.var or [], vars_json=args.vars_json or [])
    except PromptError as error:
        print(str(error), file=sys.stderr)
        return 1

    if args.out:
        out = Path(args.out).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"Rendered prompt: {out}")
    else:
        print(text)
    return 0


def _target_record(args: Namespace, workspace: Path) -> dict[str, object]:
    if getattr(args, "session", None):
        return resolve_record(args.session, workspace=workspace, all_workspaces=args.all)
    return active_record(workspace)


def _print_result(command: str, payload: dict[str, object]) -> None:
    if command == "status":
        print(f"Prompt mode: {payload.get('prompt_mode')}")
        print(f"Prompt path: {payload.get('prompt_path')}")
        print(f"Prompt exists: {payload.get('prompt_exists')}")
    elif command == "clear":
        print("Cleared session prompt overlay.")
    elif command == "mode":
        print(f"Prompt mode: {payload.get('prompt_mode')}")
    else:
        print(f"Prompt path: {payload.get('prompt_path')}")
