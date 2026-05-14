from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path

from clfc.cli.commands.launch import execute_record
from clfc.core.index import ResolveError, resolve_record, write_index
from clfc.core.paths import iter_transcript_files, workspace_transcripts
from clfc.core.prompt import PromptError, render_template_file
from clfc.core.transcript import summarize_transcript
from clfc.core.workspace import WorkspaceError, active_record


def run(args: Namespace) -> int:
    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else Path.cwd()
    if args.refresh:
        files = iter_transcript_files() if args.all else workspace_transcripts(workspace)
        write_index([summarize_transcript(path) for path in files])

    try:
        record = (
            resolve_record(args.session, workspace=workspace, all_workspaces=args.all)
            if args.session
            else active_record(workspace)
        )
        prompt = _build_prompt(args)
    except (ResolveError, WorkspaceError, PromptError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 1

    if not prompt.strip():
        print("Expected a prompt, --prompt-file, or --template.", file=sys.stderr)
        return 2

    return execute_record(
        record,
        workspace,
        prompt,
        model=args.model,
        effort=args.effort,
        permission_mode=args.permission_mode,
        dangerously_skip_permissions=args.dangerously_skip_permissions,
        allow_dangerously_skip_permissions=args.allow_dangerously_skip_permissions,
        fork_session=args.fork,
        name=args.name,
        bare=args.bare,
        add_dirs=args.add_dir or [],
        output_format=args.output_format,
        dry_run=args.dry_run,
        checkout_new=args.checkout_new,
        display_name=args.display_name,
    )


def _build_prompt(args: Namespace) -> str:
    parts: list[str] = []
    if args.template:
        parts.append(render_template_file(Path(args.template), var_entries=args.var or [], vars_json=args.vars_json or []))
    if args.prompt_file:
        parts.append(Path(args.prompt_file).expanduser().resolve().read_text(encoding="utf-8-sig"))
    if args.prompt:
        parts.append(" ".join(args.prompt))
    return "\n\n".join(part for part in parts if part)
