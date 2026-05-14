from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from clfc.core.summaries import EventSummary, TranscriptSummary, UsageSummary
from clfc.utils.jsonl import iter_jsonl


def summarize_transcript(path: Path, include_events: bool = False) -> TranscriptSummary:
    path = path.expanduser().resolve()
    session_id = path.stem
    summary = TranscriptSummary(path=path, session_id=session_id, project_key=path.parent.name)

    record_counts: Counter[str] = Counter()
    role_counts: Counter[str] = Counter()
    block_counts: Counter[str] = Counter()
    tool_counts: Counter[str] = Counter()
    model_counts: Counter[str] = Counter()
    usage = UsageSummary()
    seen_usage_ids: set[str] = set()
    event_index = 0

    for _, record in iter_jsonl(path):
        record_type = _string(record.get("type"))
        if record_type:
            record_counts[record_type] += 1

        if _string(record.get("sessionId")):
            summary.session_id = _string(record.get("sessionId")) or summary.session_id
        if _string(record.get("cwd")) and not summary.cwd:
            summary.cwd = _string(record.get("cwd"))
        if _string(record.get("version")):
            summary.version = _string(record.get("version"))
        if _string(record.get("gitBranch")):
            summary.git_branch = _string(record.get("gitBranch"))
        if _string(record.get("permissionMode")):
            summary.permission_mode = _string(record.get("permissionMode"))
        if _string(record.get("timestamp")):
            if summary.created_at is None:
                summary.created_at = _string(record.get("timestamp"))
            summary.updated_at = _string(record.get("timestamp"))
        if record_type == "last-prompt" and _string(record.get("leafUuid")):
            summary.leaf_uuid = _string(record.get("leafUuid"))

        event = _event_summary(event_index, record)
        event_index += 1
        if include_events:
            summary.events.append(event)

        message = record.get("message")
        if isinstance(message, dict):
            role = _string(message.get("role"))
            if role:
                role_counts[role] += 1

            model = _string(message.get("model"))
            if model:
                model_counts[model] += 1

            for block in _content_blocks(message.get("content")):
                block_type = _string(block.get("type"))
                if block_type:
                    block_counts[block_type] += 1
                if block_type == "tool_use":
                    tool_name = _string(block.get("name")) or "unknown"
                    tool_counts[tool_name] += 1
                if block_type == "tool_result" and bool(block.get("is_error")):
                    summary.tool_error_count += 1

            usage_id = _string(message.get("id")) or _string(record.get("uuid"))
            usage_payload = message.get("usage")
            if usage_id and usage_id not in seen_usage_ids and isinstance(usage_payload, dict):
                seen_usage_ids.add(usage_id)
                usage.input_tokens += _int(usage_payload.get("input_tokens"))
                usage.output_tokens += _int(usage_payload.get("output_tokens"))
                usage.cache_creation_input_tokens += _int(usage_payload.get("cache_creation_input_tokens"))
                usage.cache_read_input_tokens += _int(usage_payload.get("cache_read_input_tokens"))

    if summary.updated_at is None:
        summary.updated_at = _file_mtime(path)
    if summary.created_at is None:
        summary.created_at = summary.updated_at

    summary.record_counts = dict(sorted(record_counts.items()))
    summary.role_counts = dict(sorted(role_counts.items()))
    summary.block_counts = dict(sorted(block_counts.items()))
    summary.tool_counts = dict(sorted(tool_counts.items()))
    summary.model_counts = dict(sorted(model_counts.items()))
    summary.usage = usage
    return summary


def _event_summary(index: int, record: dict[str, Any]) -> EventSummary:
    message = record.get("message")
    blocks = _content_blocks(message.get("content")) if isinstance(message, dict) else []
    block_types: list[str] = []
    tool_names: list[str] = []
    tool_result_ids: list[str] = []
    tool_error = False

    for block in blocks:
        block_type = _string(block.get("type"))
        if block_type:
            block_types.append(block_type)
        if block_type == "tool_use":
            tool_name = _string(block.get("name"))
            if tool_name:
                tool_names.append(tool_name)
        if block_type == "tool_result":
            tool_result_id = _string(block.get("tool_use_id"))
            if tool_result_id:
                tool_result_ids.append(tool_result_id)
            tool_error = tool_error or bool(block.get("is_error"))

    role = _string(message.get("role")) if isinstance(message, dict) else None
    return EventSummary(
        index=index,
        record_type=_string(record.get("type")),
        role=role,
        operation=_string(record.get("operation")),
        uuid=_string(record.get("uuid")),
        parent_uuid=_string(record.get("parentUuid")),
        leaf_uuid=_string(record.get("leafUuid")),
        block_types=block_types,
        tool_names=tool_names,
        tool_result_ids=tool_result_ids,
        tool_error=tool_error,
    )


def _content_blocks(content: object) -> list[dict[str, Any]]:
    if isinstance(content, list):
        return [item for item in content if isinstance(item, dict)]
    if isinstance(content, str):
        return [{"type": "string-content"}]
    return []


def _string(value: object) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def _int(value: object) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return 0


def _file_mtime(path: Path) -> str:
    from datetime import datetime, timezone

    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
