from __future__ import annotations

import json
import os
import shutil
from argparse import Namespace
from pathlib import Path
from typing import Any

from clfc.core.paths import claude_config_root, claude_projects_root, workspace_transcripts


def run(args: Namespace) -> int:
    config_root = claude_config_root()
    projects_root = claude_projects_root()
    settings_path = config_root / "settings.json"
    settings = _load_json(settings_path)
    settings_env = settings.get("env") if isinstance(settings.get("env"), dict) else {}
    base_url = os.environ.get("ANTHROPIC_BASE_URL") or settings_env.get("ANTHROPIC_BASE_URL")
    auth_token = os.environ.get("ANTHROPIC_AUTH_TOKEN") or settings_env.get("ANTHROPIC_AUTH_TOKEN")
    current_transcripts = workspace_transcripts(Path.cwd(), projects_root)

    payload: dict[str, Any] = {
        "claude": {
            "path": shutil.which("claude"),
            "available": shutil.which("claude") is not None,
        },
        "ollama": {
            "path": shutil.which("ollama"),
            "available": shutil.which("ollama") is not None,
        },
        "claude_config_root": str(config_root),
        "claude_projects_root": str(projects_root),
        "claude_projects_root_exists": projects_root.exists(),
        "settings_path": str(settings_path),
        "settings_exists": settings_path.exists(),
        "anthropic_base_url": base_url,
        "anthropic_auth_token_configured": bool(auth_token),
        "configured_model": settings.get("model"),
        "current_workspace": str(Path.cwd()),
        "current_workspace_transcripts": len(current_transcripts),
    }

    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    _print_human(payload)
    return 0


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return {}


def _print_human(payload: dict[str, Any]) -> None:
    claude = payload["claude"]
    ollama = payload["ollama"]
    print("ClaudeForClaude doctor")
    print(f"  claude: {'ok' if claude['available'] else 'missing'} {claude['path'] or ''}".rstrip())
    print(f"  ollama: {'ok' if ollama['available'] else 'missing'} {ollama['path'] or ''}".rstrip())
    print(f"  config root: {payload['claude_config_root']}")
    print(f"  projects root: {payload['claude_projects_root']} ({'exists' if payload['claude_projects_root_exists'] else 'missing'})")
    print(f"  settings: {payload['settings_path']} ({'exists' if payload['settings_exists'] else 'missing'})")
    print(f"  ANTHROPIC_BASE_URL: {payload['anthropic_base_url'] or '<not configured>'}")
    print(f"  ANTHROPIC_AUTH_TOKEN: {'configured' if payload['anthropic_auth_token_configured'] else '<not configured>'}")
    print(f"  configured model: {payload['configured_model'] or '<not configured>'}")
    print(f"  current workspace transcripts: {payload['current_workspace_transcripts']}")
