from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class PromptError(ValueError):
    pass


def render_template_file(
    template_path: Path,
    *,
    var_entries: list[str] | None = None,
    vars_json: list[str] | None = None,
) -> str:
    template_path = template_path.expanduser().resolve()
    if not template_path.is_file():
        raise PromptError(f"Prompt template is not a file: {template_path}")
    return render_template(
        template_path.read_text(encoding="utf-8-sig"),
        parse_template_values(var_entries=var_entries, vars_json=vars_json),
    )


def render_template(template: str, values: Mapping[str, Any]) -> str:
    try:
        return template.format_map(_StrictMapping(values))
    except KeyError as error:
        raise PromptError(f"Missing template value: {error.args[0]}") from error
    except ValueError as error:
        raise PromptError(f"Invalid prompt template: {error}") from error


def parse_template_values(
    *,
    var_entries: list[str] | None = None,
    vars_json: list[str] | None = None,
) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for source in vars_json or []:
        values.update(_load_json_values(source))
    for entry in var_entries or []:
        if "=" not in entry:
            raise PromptError(f"Expected --var in key=value form: {entry!r}")
        key, value = entry.split("=", 1)
        key = key.strip()
        if not key:
            raise PromptError(f"Expected non-empty --var key: {entry!r}")
        values[key] = value
    return values


def _load_json_values(source: str) -> dict[str, Any]:
    raw = _read_json_source(source)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise PromptError(f"Invalid JSON variables: {error}") from error
    if not isinstance(payload, dict):
        raise PromptError("JSON variables must be an object/dictionary.")
    return {str(key): _normalize_value(value) for key, value in payload.items()}


def _read_json_source(source: str) -> str:
    if source.startswith("@"):
        return _read_json_file(Path(source[1:]))
    candidate = Path(source).expanduser()
    if candidate.is_file():
        return _read_json_file(candidate)
    return source


def _read_json_file(path: Path) -> str:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise PromptError(f"Variables JSON file is not a file: {path}")
    return path.read_text(encoding="utf-8-sig")


def _normalize_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=2)
    return value


class _StrictMapping(dict[str, Any]):
    def __init__(self, values: Mapping[str, Any]) -> None:
        super().__init__(values)

    def __missing__(self, key: str) -> Any:
        raise KeyError(key)
