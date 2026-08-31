from __future__ import annotations

from html import escape
from pathlib import Path

from .analysis import CategoryTrend


def acceleration_chart(
    trends: list[CategoryTrend], path: str | Path, *, top_n: int = 15
) -> None:
    data = trends[:top_n]
    width, left, right, row_height = 980, 115, 55, 35
    height = 105 + row_height * len(data)
    chart_width = width - left - right
    values = [100 * item.acceleration for item in data]
    minimum, maximum = min(0.0, min(values)), max(0.0, max(values))
    span = maximum - minimum or 1.0

    def x(value: float) -> float:
        return left + (value - minimum) / span * chart_width

    zero = x(0.0)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<style>text{font-family:Inter,Segoe UI,Arial,sans-serif;fill:#172033}.label{font-size:14px}.value{font-size:13px;font-weight:600}.title{font-size:24px;font-weight:700}.sub{font-size:13px;fill:#526079}</style>',
        '<text class="title" x="30" y="38">Acceleration in arXiv mathematics submission growth</text>',
        '<text class="sub" x="30" y="62">2025-2026 growth minus the 2024-2025 baseline; percentage points</text>',
        f'<line x1="{zero:.1f}" x2="{zero:.1f}" y1="82" y2="{height - 25}" stroke="#9aa5b5"/>',
    ]
    for index, (item, value) in enumerate(zip(data, values)):
        y = 90 + index * row_height
        end = x(value)
        bar_x, bar_w = min(zero, end), max(1.0, abs(end - zero))
        color = "#2563eb" if value >= 0 else "#dc2626"
        parts.append(f'<text class="label" x="25" y="{y + 18}">{escape(item.category)}</text>')
        parts.append(
            f'<rect x="{bar_x:.1f}" y="{y}" width="{bar_w:.1f}" height="22" rx="4" fill="{color}" opacity="0.88"/>'
        )
        value_x = end + 7 if value >= 0 else end - 7
        anchor = "start" if value >= 0 else "end"
        parts.append(
            f'<text class="value" text-anchor="{anchor}" x="{value_x:.1f}" y="{y + 16}">{value:+.1f} pp</text>'
        )
    parts.append("</svg>")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(parts), encoding="utf-8")

