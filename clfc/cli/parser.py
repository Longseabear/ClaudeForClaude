from __future__ import annotations

import argparse

from clfc.cli.commands import doctor, index, inspect, list, scan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="clfc",
        description="ClaudeForClaude: safe local tooling for Claude Code transcripts.",
    )
    subparsers = parser.add_subparsers(dest="command")

    doctor_parser = subparsers.add_parser("doctor", help="Check local Claude Code and Ollama readiness.")
    doctor_parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    doctor_parser.set_defaults(handler=doctor.run)

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
