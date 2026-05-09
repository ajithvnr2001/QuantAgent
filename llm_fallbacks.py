from __future__ import annotations

from typing import Any


def format_kline_rows(kline_data: dict[str, Any], max_rows: int = 45) -> str:
    """Format recent OHLC rows for text-only LLM fallback analysis."""
    columns = ["Datetime", "Open", "High", "Low", "Close"]
    values = {column: list(kline_data.get(column, [])) for column in columns}
    row_count = min((len(values[column]) for column in columns), default=0)
    if row_count == 0:
        return "No OHLC rows were available."

    start = max(0, row_count - max_rows)
    lines = ["Datetime | Open | High | Low | Close"]
    for idx in range(start, row_count):
        row = []
        for column in columns:
            value = values[column][idx]
            if isinstance(value, float):
                row.append(f"{value:.4f}")
            else:
                row.append(str(value))
        lines.append(" | ".join(row))
    return "\n".join(lines)


def is_image_input_error(error: Exception) -> bool:
    error_text = str(error).lower()
    image_markers = ("image", "image_url", "vision", "multimodal")
    rejection_markers = (
        "unsupported",
        "not supported",
        "invalid",
        "content type",
        "bad request",
        "400",
    )
    return any(marker in error_text for marker in image_markers) and any(
        marker in error_text for marker in rejection_markers
    )
