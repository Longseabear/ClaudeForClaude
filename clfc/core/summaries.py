from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class UsageSummary:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_creation_input_tokens": self.cache_creation_input_tokens,
            "cache_read_input_tokens": self.cache_read_input_tokens,
        }


@dataclass
class EventSummary:
    index: int
    record_type: str | None
    role: str | None = None
    operation: str | None = None
    uuid: str | None = None
    parent_uuid: str | None = None
    leaf_uuid: str | None = None
    block_types: list[str] = field(default_factory=list)
    tool_names: list[str] = field(default_factory=list)
    tool_result_ids: list[str] = field(default_factory=list)
    tool_error: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "record_type": self.record_type,
            "role": self.role,
            "operation": self.operation,
            "uuid": self.uuid,
            "parent_uuid": self.parent_uuid,
            "leaf_uuid": self.leaf_uuid,
            "block_types": self.block_types,
            "tool_names": self.tool_names,
            "tool_result_ids": self.tool_result_ids,
            "tool_error": self.tool_error,
        }


@dataclass
class TranscriptSummary:
    path: Path
    session_id: str
    project_key: str
    cwd: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    version: str | None = None
    git_branch: str | None = None
    permission_mode: str | None = None
    record_counts: dict[str, int] = field(default_factory=dict)
    role_counts: dict[str, int] = field(default_factory=dict)
    block_counts: dict[str, int] = field(default_factory=dict)
    tool_counts: dict[str, int] = field(default_factory=dict)
    tool_error_count: int = 0
    model_counts: dict[str, int] = field(default_factory=dict)
    usage: UsageSummary = field(default_factory=UsageSummary)
    leaf_uuid: str | None = None
    events: list[EventSummary] = field(default_factory=list)

    @property
    def user_messages(self) -> int:
        return self.role_counts.get("user", 0)

    @property
    def assistant_messages(self) -> int:
        return self.role_counts.get("assistant", 0)

    @property
    def tool_calls(self) -> int:
        return sum(self.tool_counts.values())

    def to_dict(self, include_events: bool = False) -> dict[str, object]:
        payload: dict[str, object] = {
            "session_id": self.session_id,
            "path": str(self.path),
            "project_key": self.project_key,
            "cwd": self.cwd,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version,
            "git_branch": self.git_branch,
            "permission_mode": self.permission_mode,
            "record_counts": self.record_counts,
            "role_counts": self.role_counts,
            "block_counts": self.block_counts,
            "tool_counts": self.tool_counts,
            "tool_error_count": self.tool_error_count,
            "model_counts": self.model_counts,
            "usage": self.usage.to_dict(),
            "leaf_uuid": self.leaf_uuid,
        }
        if include_events:
            payload["events"] = [event.to_dict() for event in self.events]
        return payload
