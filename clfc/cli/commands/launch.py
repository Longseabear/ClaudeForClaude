from __future__ import annotations

import subprocess
from pathlib import Path

from clfc.core.index import read_workspace_records, set_display_name, write_index
from clfc.core.paths import workspace_transcripts
from clfc.core.runtime import prepare_launch_workspace, prompt_overrides
from clfc.core.runner import InteractiveOptions, build_interactive_command, run_interactive
from clfc.core.transcript import summarize_transcript
from clfc.core.workspace import set_active_session


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
    checkout_new: bool = False,
    display_name: str | None = None,
) -> int:
    session_id = str(record.get("session_id") or "")
    launch_workspace, real_workspace, _ = prepare_launch_workspace(record, fallback_workspace)
    combined_add_dirs = _combined_add_dirs(real_workspace, add_dirs or [])
    system_prompt, append_system_prompt = prompt_overrides(record, fallback_workspace)
    resume, explicit_session_id = _launch_session_args(record, fork_session=fork_session)
    options = InteractiveOptions(
        workspace=launch_workspace,
        model=model,
        effort=effort,
        permission_mode=permission_mode,
        dangerously_skip_permissions=dangerously_skip_permissions,
        allow_dangerously_skip_permissions=allow_dangerously_skip_permissions,
        resume=resume,
        session_id=explicit_session_id,
        fork_session=fork_session,
        name=name,
        bare=bare,
        add_dirs=combined_add_dirs,
        system_prompt=system_prompt,
        append_system_prompt=append_system_prompt,
    )

    command = build_interactive_command(options)
    if dry_run:
        print(subprocess.list2cmdline(command))
        print(f"cwd: {launch_workspace}")
        if fork_session and (checkout_new or display_name):
            print("post-fork: would refresh index and update the new fork after Claude exits")
        return 0
    if "--dangerously-skip-permissions" in command:
        print("WARNING: launching Claude Code with permission checks bypassed.")
    before_session_ids = _transcript_session_ids(real_workspace) if fork_session and (checkout_new or display_name) else set()
    status = run_interactive(options)
    if status == 0 and fork_session and (checkout_new or display_name):
        _postprocess_fork(
            before_session_ids,
            original_session_id=session_id,
            real_workspace=real_workspace,
            checkout_workspace=fallback_workspace,
            checkout_new=checkout_new,
            display_name=display_name,
        )
    return status


def execute_record(
    record: dict[str, object],
    fallback_workspace: Path,
    prompt: str,
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
    output_format: str | None = None,
    dry_run: bool = False,
    checkout_new: bool = False,
    display_name: str | None = None,
) -> int:
    session_id = str(record.get("session_id") or "")
    launch_workspace, real_workspace, _ = prepare_launch_workspace(record, fallback_workspace)
    combined_add_dirs = _combined_add_dirs(real_workspace, add_dirs or [])
    system_prompt, append_system_prompt = prompt_overrides(record, fallback_workspace)
    resume, explicit_session_id = _launch_session_args(record, fork_session=fork_session)
    options = InteractiveOptions(
        workspace=launch_workspace,
        model=model,
        effort=effort,
        permission_mode=permission_mode,
        dangerously_skip_permissions=dangerously_skip_permissions,
        allow_dangerously_skip_permissions=allow_dangerously_skip_permissions,
        resume=resume,
        session_id=explicit_session_id,
        fork_session=fork_session,
        name=name,
        bare=bare,
        add_dirs=combined_add_dirs,
        print_response=True,
        prompt=prompt,
        output_format=output_format,
        system_prompt=system_prompt,
        append_system_prompt=append_system_prompt,
    )

    command = build_interactive_command(options)
    if dry_run:
        print(subprocess.list2cmdline(command))
        print(f"cwd: {launch_workspace}")
        if fork_session and (checkout_new or display_name):
            print("post-fork: would refresh index and update the new fork after Claude exits")
        return 0
    if "--dangerously-skip-permissions" in command:
        print("WARNING: launching Claude Code with permission checks bypassed.")
    before_session_ids = _transcript_session_ids(real_workspace) if fork_session and (checkout_new or display_name) else set()
    status = run_interactive(options)
    if status == 0 and fork_session and (checkout_new or display_name):
        _postprocess_fork(
            before_session_ids,
            original_session_id=session_id,
            real_workspace=real_workspace,
            checkout_workspace=fallback_workspace,
            checkout_new=checkout_new,
            display_name=display_name,
        )
    return status


def _combined_add_dirs(real_workspace: Path, add_dirs: list[str]) -> list[str]:
    real = str(real_workspace)
    normalized = {real.lower()}
    combined = [real]
    for value in add_dirs:
        if value.lower() not in normalized:
            combined.append(value)
            normalized.add(value.lower())
    return combined


def _launch_session_args(record: dict[str, object], *, fork_session: bool) -> tuple[str | None, str | None]:
    session_id = str(record.get("session_id") or "")
    if record.get("launch_mode") == "session-id" and not fork_session:
        return None, session_id
    return session_id, None


def _transcript_session_ids(workspace: Path) -> set[str]:
    return {path.stem for path in workspace_transcripts(workspace)}


def _postprocess_fork(
    before_session_ids: set[str],
    *,
    original_session_id: str,
    real_workspace: Path,
    checkout_workspace: Path,
    checkout_new: bool,
    display_name: str | None,
) -> None:
    files = workspace_transcripts(real_workspace)
    write_index([summarize_transcript(path) for path in files])
    records = read_workspace_records(real_workspace)
    candidates = [
        record
        for record in records
        if str(record.get("session_id") or "") not in before_session_ids
        and str(record.get("session_id") or "") != original_session_id
    ]
    if not candidates:
        print("No new fork transcript was detected after launch.")
        return

    record = candidates[0]
    session_id = str(record.get("session_id") or "")
    if display_name:
        record = set_display_name(session_id, display_name, workspace=real_workspace)
        print(f"Named forked session {session_id}: {display_name}")
    if checkout_new:
        set_active_session(checkout_workspace, record)
        print(f"Checked out forked session {session_id}")
    print(f"Indexed forked session {session_id}")
