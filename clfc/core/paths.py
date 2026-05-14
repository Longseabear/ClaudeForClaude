from __future__ import annotations

import os
from pathlib import Path

from clfc.utils.jsonl import iter_jsonl


def claude_config_root(env: dict[str, str] | None = None) -> Path:
    env = env or os.environ
    configured = env.get("CLAUDE_CONFIG_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".claude"


def claude_projects_root(env: dict[str, str] | None = None) -> Path:
    return claude_config_root(env) / "projects"


def iter_transcript_files(projects_root: Path | None = None) -> list[Path]:
    root = projects_root or claude_projects_root()
    if not root.exists():
        return []
    return sorted(root.rglob("*.jsonl"), key=lambda path: path.stat().st_mtime, reverse=True)


def normalize_workspace(path: Path) -> str:
    return os.path.normcase(str(path.expanduser().resolve()))


def transcript_cwd(path: Path) -> str | None:
    for _, record in iter_jsonl(path):
        cwd = record.get("cwd")
        if isinstance(cwd, str) and cwd:
            return cwd
    return None


def workspace_transcripts(workspace: Path, projects_root: Path | None = None) -> list[Path]:
    wanted = normalize_workspace(workspace)
    matches: list[Path] = []
    for path in iter_transcript_files(projects_root):
        cwd = transcript_cwd(path)
        if cwd and normalize_workspace(Path(cwd)) == wanted:
            matches.append(path)
    return matches
