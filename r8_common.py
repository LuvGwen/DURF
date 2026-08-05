"""Shared helpers for R8 final integrated analysis.

R8 is a synthesis stage. It reads existing result artifacts and creates final
analysis tables, reports, figures, and R9 input files without running new
gameplay simulations or changing policy defaults.
"""

from __future__ import annotations

import csv
import json
import math
import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "results" / "final_integrated_analysis_stage_r8"
FIGURE_DIR = OUTPUT_DIR / "figures"
R9_PACK_DIR = OUTPUT_DIR / "r9_input_pack"
RESEARCH_DIR = ROOT / "results" / "research_progress"

EXPLICIT_MISSING = {
    "not_reported",
    "not_applicable",
    "insufficient_data",
    "descriptive_only",
}

R4_EXPECTED_MANIFEST_HASH = "eee8007693ec6a484632f61444a53f6f8b1b9feb64b18c865f0edf704a15c7cd"
R5_EXPECTED_METRIC_MANIFEST_HASH = "4b48f5aae165d6c30d5a13cd2e9c3e01f5b595ddbfeb93f7c1832b018f6861bf"
R62_EXPECTED_CONFIGURATION_HASH = "0d5e284c625dd63181c6ee852e565a10506271cba3b3684da3b612c634d2e537"


def read_csv(path: str | Path) -> list[dict[str, str]]:
    path = ROOT / path if not isinstance(path, Path) else path
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: str | Path, rows: list[dict[str, str]], fieldnames: list[str] | None = None) -> None:
    path = ROOT / path if not isinstance(path, Path) else path
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
    normalized_rows = []
    for row in rows:
        normalized_rows.append({field: row.get(field, "not_reported") for field in fieldnames})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized_rows)


def write_text(path: str | Path, text: str) -> None:
    path = ROOT / path if not isinstance(path, Path) else path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def path_exists(path: str | Path) -> bool:
    path = ROOT / path if not isinstance(path, Path) else path
    return path.exists()


def row_count(path: str | Path) -> int:
    return len(read_csv(path))


def unique_count(path: str | Path, column: str) -> int:
    rows = read_csv(path)
    if not rows or column not in rows[0]:
        return 0
    return len({row[column] for row in rows if row.get(column, "")})


def json_field(path: str | Path, key: str) -> str:
    path = ROOT / path if not isinstance(path, Path) else path
    data = json.loads(path.read_text(encoding="utf-8"))
    return str(data.get(key, "not_reported"))


def safe_float(value: str, default: float | None = None) -> float | None:
    try:
        if value in {"", "NA", "not_reported", "not_applicable", "insufficient_data"}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt_float(value: str | float | None, digits: int = 4) -> str:
    number = safe_float(str(value), None) if not isinstance(value, float) else value
    if number is None or math.isnan(number):
        return "not_reported"
    return f"{number:.{digits}f}"


def fmt_pp(value: str | float | None, digits: int = 2) -> str:
    number = safe_float(str(value), None) if not isinstance(value, float) else value
    if number is None or math.isnan(number):
        return "not_reported"
    return f"{number * 100:.{digits}}%"


def ci_text(low: str, high: str, digits: int = 4) -> str:
    if not low or not high:
        return "not_reported"
    return f"[{fmt_float(low, digits)}, {fmt_float(high, digits)}]"


def markdown_table(rows: list[dict[str, str]], columns: list[tuple[str, str]]) -> str:
    header = "| " + " | ".join(label for _, label in columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| "
        + " | ".join(str(row.get(key, "not_reported")).replace("|", "/") for key, _ in columns)
        + " |"
        for row in rows
    ]
    return "\n".join([header, divider] + body)


def get_row(rows: list[dict[str, str]], **criteria: str) -> dict[str, str]:
    for row in rows:
        if all(row.get(key) == value for key, value in criteria.items()):
            return row
    raise KeyError(f"Row not found: {criteria}")


def write_simple_svg(
    path: str | Path,
    title: str,
    rows: list[tuple[str, float]],
    source_data: str,
    width: int = 980,
    height: int = 560,
) -> None:
    path = ROOT / path if not isinstance(path, Path) else path
    path.parent.mkdir(parents=True, exist_ok=True)
    max_value = max([abs(value) for _, value in rows] + [1.0])
    left = 260
    top = 70
    bar_h = 24
    gap = 14
    plot_w = width - left - 80
    total_h = max(height, top + len(rows) * (bar_h + gap) + 82)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{total_h}" viewBox="0 0 {width} {total_h}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="24" y="36" font-family="Arial" font-size="20" font-weight="700" fill="#172033">{title}</text>',
        f'<text x="24" y="{total_h - 24}" font-family="Arial" font-size="11" fill="#526070">Source: {source_data}</text>',
    ]
    zero_x = left + plot_w / 2 if any(value < 0 for _, value in rows) else left
    if any(value < 0 for _, value in rows):
        parts.append(f'<line x1="{zero_x}" y1="{top - 10}" x2="{zero_x}" y2="{total_h - 60}" stroke="#94a3b8" stroke-width="1"/>')
    for idx, (label, value) in enumerate(rows):
        y = top + idx * (bar_h + gap)
        parts.append(f'<text x="24" y="{y + 17}" font-family="Arial" font-size="13" fill="#263445">{label}</text>')
        if value >= 0:
            x = zero_x
            bar_w = (value / max_value) * (plot_w if zero_x == left else plot_w / 2)
            color = "#2f6fbb"
        else:
            bar_w = (abs(value) / max_value) * (plot_w / 2)
            x = zero_x - bar_w
            color = "#b64d4d"
        parts.append(f'<rect x="{x:.1f}" y="{y}" width="{bar_w:.1f}" height="{bar_h}" rx="3" fill="{color}"/>')
        parts.append(f'<text x="{x + bar_w + 8:.1f}" y="{y + 17}" font-family="Arial" font-size="13" fill="#263445">{value:.3g}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts) + "\n", encoding="utf-8")


def write_placeholder_png(path: str | Path, width: int = 960, height: int = 540) -> None:
    """Write a simple valid PNG using only the standard library."""
    path = ROOT / path if not isinstance(path, Path) else path
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for y in range(height):
        scanline = bytearray([0])
        for x in range(width):
            if 70 < y < height - 70 and 80 < x < width - 80:
                r, g, b = (236, 244, 255)
            else:
                r, g, b = (255, 255, 255)
            if x % 160 < 80 and height - 170 < y < height - 90:
                r, g, b = (47, 111, 187)
            scanline.extend((r, g, b))
        rows.append(bytes(scanline))
    raw = b"".join(rows)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    payload = b"\x89PNG\r\n\x1a\n"
    payload += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    payload += chunk(b"IDAT", zlib.compress(raw, 9))
    payload += chunk(b"IEND", b"")
    path.write_bytes(payload)


def append_unique_section(path: str | Path, marker: str, content: str) -> None:
    path = ROOT / path if not isinstance(path, Path) else path
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if marker not in existing:
        path.write_text(existing.rstrip() + "\n\n" + content.strip() + "\n", encoding="utf-8")
