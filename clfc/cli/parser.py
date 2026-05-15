from __future__ import annotations

import argparse

from clfc.cli.commands import (
    add,
    checkout,
    current,
    doctor,
    execute,
    fork,
    gc,
    index,
    init,
    inspect,
    interactive,
    list,
    memory,
    name,
    open as session_open,
    prompt,
    resume,
    scan,
    settings,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="clfc",
        description="ClaudeForClaude: safe local tooling for Claude Code transcripts.",
    )
    subparsers = parser.add_subparsers(dest="command")

    doctor_parser = subparsers.add_parser("doctor", help="Check local Claude Code and Ollama readiness.")
    doctor_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    doctor_parser.set_defaults(handler=doctor.run)

    init_parser = subparsers.add_parser("init", help="Initialize local .clfc workspace metadata.")
    init_parser.add_argument("--workspace", help="Workspace path. Defaults to the current directory.")
    init_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    init_parser.set_defaults(handler=init.run)

    interactive_parser = subparsers.add_parser(
        "interactive",
        aliases=["chat"],
        help="Launch an interactive Claude Code session with CLFC defaults.",
    )
    interactive_parser.add_argument("--workspace", help="Workspace path. Defaults to the current directory.")
    interactive_parser.add_argument("--model", help="Claude Code model override.")
    interactive_parser.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"], help="Effort override.")
    interactive_parser.add_argument(
        "--permission-mode",
        choices=["acceptEdits", "auto", "bypassPermissions", "default", "dontAsk", "plan"],
        help="Claude Code permission mode override.",
    )
    interactive_parser.add_argument(
        "--dangerously-skip-permissions",
        action="store_true",
        help="Bypass all Claude Code permission checks for this launch.",
    )
    interactive_parser.add_argument(
        "--allow-dangerously-skip-permissions",
        action="store_true",
        help="Allow bypass mode to be selected in Claude Code without enabling it by default.",
    )
    interactive_parser.add_argument("--resume", help="Resume a Claude Code session id or search value.")
    interactive_parser.add_argument("-c", "--continue", action="store_true", dest="continue_latest", help="Continue the most recent conversation.")
    interactive_parser.add_argument("--name", help="Set Claude Code session display name.")
    interactive_parser.add_argument("--bare", action="store_true", help="Launch Claude Code in bare mode.")
    interactive_parser.add_argument("--add-dir", action="append", help="Additional directory to allow. Repeatable.")
    interactive_parser.add_argument("--dry-run", action="store_true", help="Print the claude command without launching it.")
    interactive_parser.add_argument("extra_args", nargs=argparse.REMAINDER, help="Extra args after `--` are passed to claude.")
    interactive_parser.set_defaults(handler=interactive.run)

    add_parser = subparsers.add_parser(
        "add",
        help="Add a named CLFC session, creating a new Claude session id when none is provided.",
    )
    add_parser.add_argument("display_name", help="CLFC display name to create or assign.")
    add_parser.add_argument("session", nargs="?", help="Existing indexed session id/prefix/display name, or a full unindexed UUID.")
    add_parser.add_argument("--workspace", help="Workspace path. Defaults to the current directory.")
    add_parser.add_argument("-a", "--all", action="store_true", help="Resolve an existing session across all indexed workspaces.")
    add_parser.add_argument("--refresh", action="store_true", help="Refresh the index before resolving an existing session.")
    add_parser.add_argument("--checkout", action="store_true", help="Check out the added/named session immediately.")
    add_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    add_parser.set_defaults(handler=add.run)

    exec_parser = subparsers.add_parser(
        "exec",
        help="Run a non-interactive prompt against the checked-out or selected session.",
    )
    exec_parser.add_argument("prompt", nargs="*", help="Prompt text. Quote it as one argument for best results.")
    exec_parser.add_argument("--session", help="Session id, unique prefix, or display name. Defaults to the checked-out session.")
    exec_parser.add_argument("--workspace", help="Workspace path to resolve within. Defaults to the current directory.")
    exec_parser.add_argument("-a", "--all", action="store_true", help="Resolve across all indexed workspaces.")
    exec_parser.add_argument("--refresh", action="store_true", help="Refresh the index before resolving.")
    exec_parser.add_argument("--prompt-file", help="Read prompt text from a file.")
    exec_parser.add_argument("--template", help="Render a prompt template file before execution.")
    exec_parser.add_argument("--var", action="append", help="Template variable in key=value form. Repeatable.")
    exec_parser.add_argument("--vars-json", action="append", help="Template variables as JSON, @path, or a JSON file path. Repeatable.")
    exec_parser.add_argument("--fork", action="store_true", help="Fork the session for this execution.")
    exec_parser.add_argument("--checkout-new", action="store_true", help="After a successful fork, checkout the new forked session if detected.")
    exec_parser.add_argument("--display-name", help="After a successful fork, assign this CLFC display name to the new session.")
    exec_parser.add_argument("--output-format", choices=["text", "json", "stream-json"], help="Claude Code non-interactive output format.")
    exec_parser.add_argument("--model", help="Claude Code model override.")
    exec_parser.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"], help="Effort override.")
    exec_parser.add_argument(
        "--permission-mode",
        choices=["acceptEdits", "auto", "bypassPermissions", "default", "dontAsk", "plan"],
        help="Claude Code permission mode override.",
    )
    exec_parser.add_argument(
        "--dangerously-skip-permissions",
        action="store_true",
        help="Bypass all Claude Code permission checks for this execution.",
    )
    exec_parser.add_argument(
        "--allow-dangerously-skip-permissions",
        action="store_true",
        help="Allow bypass mode to be selected in Claude Code without enabling it by default.",
    )
    exec_parser.add_argument("--name", help="Set Claude Code session display name.")
    exec_parser.add_argument("--bare", action="store_true", help="Launch Claude Code in bare mode.")
    exec_parser.add_argument("--add-dir", action="append", help="Additional directory to allow. Repeatable.")
    exec_parser.add_argument("--dry-run", action="store_true", help="Print the claude command without launching it.")
    exec_parser.set_defaults(handler=execute.run)

    resume_parser = subparsers.add_parser(
        "resume",
        help="Resume an indexed Claude Code session by id or unique prefix.",
    )
    resume_parser.add_argument("session", nargs="?", help="Session id or unique prefix from `clfc list`. Defaults to the checked-out session.")
    resume_parser.add_argument("--workspace", help="Workspace path to resolve within. Defaults to the current directory.")
    resume_parser.add_argument("-a", "--all", action="store_true", help="Resolve across all indexed workspaces.")
    resume_parser.add_argument("--refresh", action="store_true", help="Refresh the index before resolving.")
    resume_parser.add_argument("--fork", action="store_true", help="Fork the session instead of appending to it.")
    resume_parser.add_argument("--model", help="Claude Code model override.")
    resume_parser.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"], help="Effort override.")
    resume_parser.add_argument(
        "--permission-mode",
        choices=["acceptEdits", "auto", "bypassPermissions", "default", "dontAsk", "plan"],
        help="Claude Code permission mode override.",
    )
    resume_parser.add_argument(
        "--dangerously-skip-permissions",
        action="store_true",
        help="Bypass all Claude Code permission checks for this launch.",
    )
    resume_parser.add_argument(
        "--allow-dangerously-skip-permissions",
        action="store_true",
        help="Allow bypass mode to be selected in Claude Code without enabling it by default.",
    )
    resume_parser.add_argument("--name", help="Set Claude Code session display name.")
    resume_parser.add_argument("--bare", action="store_true", help="Launch Claude Code in bare mode.")
    resume_parser.add_argument("--add-dir", action="append", help="Additional directory to allow. Repeatable.")
    resume_parser.add_argument("--dry-run", action="store_true", help="Print the claude command without launching it.")
    resume_parser.add_argument("--checkout-new", action="store_true", help="With --fork, checkout the new forked session if detected.")
    resume_parser.add_argument("--display-name", help="With --fork, assign this CLFC display name to the new session.")
    resume_parser.set_defaults(handler=resume.run)

    fork_parser = subparsers.add_parser(
        "fork",
        help="Fork an indexed or checked-out Claude Code session.",
    )
    fork_parser.add_argument("session", nargs="?", help="Session id or unique prefix. Defaults to the checked-out session.")
    fork_parser.add_argument("--workspace", help="Workspace path to resolve within. Defaults to the current directory.")
    fork_parser.add_argument("-a", "--all", action="store_true", help="Resolve across all indexed workspaces.")
    fork_parser.add_argument("--refresh", action="store_true", help="Refresh the index before resolving.")
    fork_parser.add_argument("--model", help="Claude Code model override.")
    fork_parser.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"], help="Effort override.")
    fork_parser.add_argument(
        "--permission-mode",
        choices=["acceptEdits", "auto", "bypassPermissions", "default", "dontAsk", "plan"],
        help="Claude Code permission mode override.",
    )
    fork_parser.add_argument(
        "--dangerously-skip-permissions",
        action="store_true",
        help="Bypass all Claude Code permission checks for this launch.",
    )
    fork_parser.add_argument(
        "--allow-dangerously-skip-permissions",
        action="store_true",
        help="Allow bypass mode to be selected in Claude Code without enabling it by default.",
    )
    fork_parser.add_argument("--name", help="Set Claude Code session display name.")
    fork_parser.add_argument("--bare", action="store_true", help="Launch Claude Code in bare mode.")
    fork_parser.add_argument("--add-dir", action="append", help="Additional directory to allow. Repeatable.")
    fork_parser.add_argument("--dry-run", action="store_true", help="Print the claude command without launching it.")
    fork_parser.add_argument("--checkout-new", action="store_true", help="After launch, checkout the new forked session if detected.")
    fork_parser.add_argument("--display-name", help="After launch, assign this CLFC display name to the new session.")
    fork_parser.set_defaults(handler=fork.run)

    checkout_parser = subparsers.add_parser("checkout", help="Set the active CLFC session for this workspace.")
    checkout_parser.add_argument("session", nargs="?", help="Session id, unique prefix, or display name.")
    checkout_parser.add_argument("--clear", action="store_true", help="Clear the active session.")
    checkout_parser.add_argument("--workspace", help="Workspace path. Defaults to the current directory.")
    checkout_parser.add_argument("-a", "--all", action="store_true", help="Resolve across all indexed workspaces.")
    checkout_parser.add_argument("--refresh", action="store_true", help="Refresh the index before resolving.")
    checkout_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    checkout_parser.set_defaults(handler=checkout.run)

    current_parser = subparsers.add_parser(
        "current",
        aliases=["status"],
        help="Show the active CLFC session for this workspace.",
    )
    current_parser.add_argument("--workspace", help="Workspace path. Defaults to the current directory.")
    current_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    current_parser.set_defaults(handler=current.run)

    memory_parser = subparsers.add_parser("memory", help="Manage session-local CLAUDE.md handling.")
    memory_subparsers = memory_parser.add_subparsers(dest="memory_command")

    memory_status = memory_subparsers.add_parser("status", help="Show session memory status.")
    _add_memory_target_args(memory_status)
    memory_status.set_defaults(handler=memory.run)

    memory_init = memory_subparsers.add_parser("init", help="Create a manual session-local CLAUDE.md.")
    _add_memory_target_args(memory_init)
    memory_init.set_defaults(handler=memory.run)

    memory_clone = memory_subparsers.add_parser("clone", help="Copy a file into session-local CLAUDE.md.")
    memory_clone.add_argument("source", help="Source markdown file.")
    _add_memory_target_args(memory_clone)
    memory_clone.set_defaults(handler=memory.run)

    memory_clear = memory_subparsers.add_parser("clear", help="Remove session-local CLAUDE.md and return to sync mode.")
    _add_memory_target_args(memory_clear)
    memory_clear.set_defaults(handler=memory.run)

    memory_mode = memory_subparsers.add_parser("mode", help="Set memory mode for a session.")
    memory_mode.add_argument("mode", choices=["sync", "manual"])
    _add_memory_target_args(memory_mode)
    memory_mode.set_defaults(handler=memory.run)

    prompt_parser = subparsers.add_parser("prompt", help="Manage session prompt overlays and render prompt templates.")
    prompt_subparsers = prompt_parser.add_subparsers(dest="prompt_command")

    prompt_status = prompt_subparsers.add_parser("status", help="Show session prompt overlay status.")
    _add_prompt_target_args(prompt_status)
    prompt_status.set_defaults(handler=prompt.run)

    prompt_init = prompt_subparsers.add_parser("init", help="Create a session-local system_prompt.md overlay.")
    _add_prompt_target_args(prompt_init)
    prompt_init.set_defaults(handler=prompt.run)

    prompt_clone = prompt_subparsers.add_parser("clone", help="Copy a file into session-local system_prompt.md.")
    prompt_clone.add_argument("source", help="Source prompt markdown file.")
    _add_prompt_target_args(prompt_clone)
    prompt_clone.set_defaults(handler=prompt.run)

    prompt_clear = prompt_subparsers.add_parser("clear", help="Remove session prompt overlay and turn prompt mode off.")
    _add_prompt_target_args(prompt_clear)
    prompt_clear.set_defaults(handler=prompt.run)

    prompt_mode = prompt_subparsers.add_parser("mode", help="Set prompt overlay mode for a session.")
    prompt_mode.add_argument("mode", choices=["off", "append", "replace"])
    _add_prompt_target_args(prompt_mode)
    prompt_mode.set_defaults(handler=prompt.run)

    prompt_render = prompt_subparsers.add_parser("render", help="Render a prompt template with dictionary values.")
    prompt_render.add_argument("template", help="Template file. Use {key} placeholders.")
    prompt_render.add_argument("--var", action="append", help="Template variable in key=value form. Repeatable.")
    prompt_render.add_argument("--vars-json", action="append", help="Template variables as JSON, @path, or a JSON file path. Repeatable.")
    prompt_render.add_argument("--out", help="Write rendered prompt to this path instead of stdout.")
    prompt_render.set_defaults(handler=prompt.run)

    prompt_apply = prompt_subparsers.add_parser("apply", help="Render a template into session-local system_prompt.md.")
    prompt_apply.add_argument("template", help="Template file. Use {key} placeholders.")
    prompt_apply.add_argument("--var", action="append", help="Template variable in key=value form. Repeatable.")
    prompt_apply.add_argument("--vars-json", action="append", help="Template variables as JSON, @path, or a JSON file path. Repeatable.")
    prompt_apply.add_argument("--mode", choices=["append", "replace"], default="append", help="Prompt overlay mode to set after applying.")
    _add_prompt_target_args(prompt_apply)
    prompt_apply.set_defaults(handler=prompt.run)

    name_parser = subparsers.add_parser("name", help="Show or set a CLFC display name for an indexed session.")
    name_parser.add_argument("session", help="Session id, unique prefix, or existing display name.")
    name_parser.add_argument("display_name", nargs="?", help="Display name to store in the CLFC index.")
    name_parser.add_argument("--clear", action="store_true", help="Remove the display name.")
    name_parser.add_argument("--workspace", help="Workspace path to resolve within. Defaults to the current directory.")
    name_parser.add_argument("-a", "--all", action="store_true", help="Resolve across all indexed workspaces.")
    name_parser.add_argument("--refresh", action="store_true", help="Refresh the index before resolving.")
    name_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    name_parser.set_defaults(handler=name.run)

    settings_parser = subparsers.add_parser("settings", help="Show or update CLFC launcher defaults.")
    settings_subparsers = settings_parser.add_subparsers(dest="settings_command")
    settings_show = settings_subparsers.add_parser("show", help="Show CLFC settings.")
    settings_show.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    settings_show.set_defaults(handler=settings.run)
    settings_set = settings_subparsers.add_parser("set", help="Set a CLFC default.")
    settings_set.add_argument(
        "key",
        choices=[
            "model",
            "effort",
            "permission-mode",
            "permission_mode",
            "dangerously-skip-permissions",
            "dangerously_skip_permissions",
            "allow-dangerously-skip-permissions",
            "allow_dangerously_skip_permissions",
        ],
    )
    settings_set.add_argument("value", help="New value. Use on/off for booleans or clear to unset strings.")
    settings_set.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    settings_set.set_defaults(handler=settings.run)

    scan_parser = subparsers.add_parser("scan", help="Summarize Claude Code transcripts without raw content.")
    scan_parser.add_argument("--workspace", help="Workspace path to match. Defaults to the current directory.")
    scan_parser.add_argument("--all", action="store_true", help="Scan every transcript under the Claude projects root.")
    scan_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    scan_parser.add_argument("--limit", type=int, default=20, help="Maximum summaries to print in table mode.")
    scan_parser.set_defaults(handler=scan.run)

    index_parser = subparsers.add_parser("index", help="Persist privacy-preserving transcript summaries.")
    index_parser.add_argument("--workspace", help="Workspace path to match. Defaults to the current directory.")
    index_parser.add_argument("--all", action="store_true", help="Index every transcript under the Claude projects root.")
    index_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    index_parser.set_defaults(handler=index.run)

    list_parser = subparsers.add_parser("list", help="List indexed Claude Code sessions.")
    list_parser.add_argument("--workspace", help="Workspace path to match. Defaults to the current directory.")
    list_parser.add_argument("-a", "--all", action="store_true", help="List indexed sessions across all workspaces.")
    list_parser.add_argument("--refresh", action="store_true", help="Refresh the index before listing.")
    list_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    list_parser.add_argument("--limit", type=int, default=20, help="Maximum records to print in table mode.")
    list_parser.set_defaults(handler=list.run)

    gc_parser = subparsers.add_parser(
        "gc",
        aliases=["prune"],
        help="Find stale CLFC index records and runtime workspaces.",
    )
    gc_parser.add_argument("--workspace", help="Workspace path to clean. Defaults to the current directory.")
    gc_parser.add_argument("-a", "--all", action="store_true", help="Scan all indexed workspaces and runtime dirs.")
    gc_parser.add_argument("--apply", action="store_true", help="Remove stale CLFC-owned files. Default is dry-run.")
    gc_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    gc_parser.set_defaults(handler=gc.run)

    open_parser = subparsers.add_parser(
        "open",
        help="Pick an indexed session and resume, fork, inspect, checkout, or name it.",
    )
    open_parser.add_argument("--workspace", help="Workspace path to match. Defaults to the current directory.")
    open_parser.add_argument("-a", "--all", action="store_true", help="Open sessions across all indexed workspaces.")
    open_parser.add_argument("--refresh", action="store_true", help="Refresh the index before listing.")
    open_parser.add_argument("--limit", type=int, default=20, help="Maximum records to show.")
    open_parser.add_argument("--select", type=int, help="1-based session number to select without prompting.")
    open_parser.add_argument(
        "--action",
        choices=["resume", "fork", "inspect", "checkout", "name", "quit"],
        help="Action to run after selecting a session.",
    )
    open_parser.add_argument("--display-name", help="Display name for name action or post-fork naming.")
    open_parser.add_argument("--launch-name", help="Claude Code session name for resume or fork launches.")
    open_parser.add_argument("--model", help="Claude Code model override.")
    open_parser.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"], help="Effort override.")
    open_parser.add_argument(
        "--permission-mode",
        choices=["acceptEdits", "auto", "bypassPermissions", "default", "dontAsk", "plan"],
        help="Claude Code permission mode override.",
    )
    open_parser.add_argument(
        "--dangerously-skip-permissions",
        action="store_true",
        help="Bypass all Claude Code permission checks for resume or fork launches.",
    )
    open_parser.add_argument(
        "--allow-dangerously-skip-permissions",
        action="store_true",
        help="Allow bypass mode to be selected in Claude Code without enabling it by default.",
    )
    open_parser.add_argument("--bare", action="store_true", help="Launch Claude Code in bare mode.")
    open_parser.add_argument("--add-dir", action="append", help="Additional directory to allow. Repeatable.")
    open_parser.add_argument("--dry-run", action="store_true", help="Print the claude command without launching it.")
    open_parser.add_argument("--checkout-new", action="store_true", help="With fork action, checkout the new forked session if detected.")
    open_parser.set_defaults(handler=session_open.run)

    inspect_parser = subparsers.add_parser("inspect", help="Show a redacted event timeline for one session.")
    inspect_parser.add_argument("session", help="Session id, unique prefix, or transcript JSONL path.")
    inspect_parser.add_argument("--workspace", help="Workspace path to match. Defaults to the current directory.")
    inspect_parser.add_argument("--all", action="store_true", help="Resolve the session across all workspaces.")
    inspect_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    inspect_parser.set_defaults(handler=inspect.run)

    return parser


def _add_memory_target_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("session", nargs="?", help="Session id, unique prefix, or display name. Defaults to the checked-out session.")
    parser.add_argument("--workspace", help="Workspace path. Defaults to the current directory.")
    parser.add_argument("-a", "--all", action="store_true", help="Resolve across all indexed workspaces.")
    parser.add_argument("--refresh", action="store_true", help="Refresh the index before resolving.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")


def _add_prompt_target_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("session", nargs="?", help="Session id, unique prefix, or display name. Defaults to the checked-out session.")
    parser.add_argument("--workspace", help="Workspace path. Defaults to the current directory.")
    parser.add_argument("-a", "--all", action="store_true", help="Resolve across all indexed workspaces.")
    parser.add_argument("--refresh", action="store_true", help="Refresh the index before resolving.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
