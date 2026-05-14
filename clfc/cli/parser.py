from __future__ import annotations

import argparse

from clfc.cli.commands import doctor, index, inspect, interactive, list, resume, scan, settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="clfc",
        description="ClaudeForClaude: safe local tooling for Claude Code transcripts.",
    )
    subparsers = parser.add_subparsers(dest="command")

    doctor_parser = subparsers.add_parser("doctor", help="Check local Claude Code and Ollama readiness.")
    doctor_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    doctor_parser.set_defaults(handler=doctor.run)

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

    resume_parser = subparsers.add_parser(
        "resume",
        help="Resume an indexed Claude Code session by id or unique prefix.",
    )
    resume_parser.add_argument("session", help="Session id or unique prefix from `clfc list`.")
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
    resume_parser.set_defaults(handler=resume.run)

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

    inspect_parser = subparsers.add_parser("inspect", help="Show a redacted event timeline for one session.")
    inspect_parser.add_argument("session", help="Session id, unique prefix, or transcript JSONL path.")
    inspect_parser.add_argument("--workspace", help="Workspace path to match. Defaults to the current directory.")
    inspect_parser.add_argument("--all", action="store_true", help="Resolve the session across all workspaces.")
    inspect_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    inspect_parser.set_defaults(handler=inspect.run)

    return parser
