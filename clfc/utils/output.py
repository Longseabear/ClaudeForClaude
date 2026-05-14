from __future__ import annotations

from collections.abc import Iterable, Sequence


def format_table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> str:
    materialized = [[_cell(value) for value in row] for row in rows]
    widths = [len(header) for header in headers]
    for row in materialized:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))

    lines = []
    lines.append("  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    lines.append("  ".join("-" * width for width in widths))
    for row in materialized:
        lines.append("  ".join(row[index].ljust(widths[index]) for index in range(len(headers))))
    return "\n".join(lines)


def _cell(value: object) -> str:
    if value is None:
        return ""
    return str(value)
