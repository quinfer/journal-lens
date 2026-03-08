#!/usr/bin/env python3
"""
Digitise the ABS AJG 2024 list from CABS_AJG_2024.pdf (ground truth).

Usage:
  # Extract from PDF using local library (no API key)
  python digitize_ajg2024_from_pdf.py "CABS_AJG_2024.pdf" -o ajg_2024_ground_truth.csv

  # Parse from already-extracted text/markdown (e.g. after LlamaParse)
  python digitize_ajg2024_from_pdf.py "CABS_AJG_2024.md" -o ajg_2024_ground_truth.csv

  # Use LlamaParse to extract PDF to markdown first (requires LLAMA_CLOUD_API_KEY):
  # From TickLab repo: python parse_llamaparse.py "path/to/CABS_AJG_2024.pdf" --format markdown
  # Then run this script on the resulting .md file.

Requires: pymupdf (pip install pymupdf) for PDF extraction. Optional: llama-parse in another env.
"""

import argparse
import csv
import re
import sys
from pathlib import Path


# Known AJG field codes from the PDF (used to detect start of data rows)
FIELD_PATTERN = re.compile(
    r"^([A-Z][A-Z0-9 &()\-]+)\t",  # Field at line start followed by tab
    re.IGNORECASE,
)
# PyMuPDF extracts each cell on its own line (no tabs); field is a full line.
FIELD_LINE_PATTERN = re.compile(r"^[A-Z][A-Z0-9 &()\-]+$")  # entire line is field code
PAGE_BREAK = re.compile(r"^--\s*\d+\s+of\s+\d+\s*--\s*$")
GRADE_PATTERN = re.compile(r"^[1234]\*?$")  # 1, 2, 3, 4, 4*


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract raw text from PDF using PyMuPDF (no API key)."""
    try:
        import fitz  # pymupdf
    except ImportError:
        raise SystemExit(
            "PDF extraction requires pymupdf. Install with: pip install pymupdf"
        )
    doc = fitz.open(pdf_path)
    parts = []
    for page in doc:
        parts.append(page.get_text())
    doc.close()
    return "\n".join(parts)


def read_input(path: str, use_pdf: bool) -> str:
    """Return full text from path (PDF or text/markdown file)."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    if use_pdf or p.suffix.lower() == ".pdf":
        return extract_text_from_pdf(str(p))
    return p.read_text(encoding="utf-8", errors="replace")


def looks_like_grade(s: str) -> bool:
    s = (s or "").strip()
    return bool(GRADE_PATTERN.match(s)) or s in ("4*", "4 *")


def _is_field_line(line: str) -> bool:
    """True if line looks like an AJG field code (e.g. ACCOUNT, ECON, BUS HIST & ECON HIST)."""
    line = (line or "").strip()
    if not line or len(line) < 2:
        return False
    if looks_like_grade(line):
        return False
    return bool(FIELD_LINE_PATTERN.match(line))


def parse_table_newline(text: str) -> list[dict]:
    """
    Parse when each cell is on its own line (PyMuPDF-style extraction).
    Row structure: Field (1 line), Journal title (1+ lines), then 10 values (1 line each).
    """
    lines = [ln.replace("\r", "").strip() for ln in text.splitlines()]
    rows = []
    i = 0

    def flush(field: str, title: str, rest: list) -> None:
        while len(rest) < 10:
            rest.append("")
        rows.append({
            "Field": field,
            "Journal Title": title,
            "AJG 2024": rest[0],
            "AJG 2021": rest[1],
            "Citescore rank": rest[2],
            "SNIP rank": rest[3],
            "SJR rank": rest[4],
            "JIF rank": rest[5],
            "SDG content (2017-21)": rest[6],
            "International co-authorship (2017-21)": rest[7],
            "Academic-non-academic collaborations (2017-21)": rest[8],
            "Citations policy docs (2017-21)": rest[9],
        })

    while i < len(lines):
        line = lines[i]
        if not line or PAGE_BREAK.match(line):
            i += 1
            continue
        if any(
            line.startswith(x)
            for x in (
                "See discussions",
                "ABS List_Journal",
                "Method ·",
                "CITATIONS",
                "READS",
                "author:",
                "All content following",
                "The user has requested",
            )
        ):
            i += 1
            continue
        if line in ("Field", "Journal Title", "AJG", "2024", "2021", "Citescore", "rank",
                    "SNIP", "SJR", "JIF", "SDG content", "(2017-21)", "International",
                    "co-authorship", "Academic-", "non-academic", "collaborations",
                    "Citations", "policy docs"):
            i += 1
            continue

        if not _is_field_line(line):
            i += 1
            continue

        field = line
        i += 1
        title_parts = []
        while i < len(lines):
            ln = lines[i]
            if not ln:
                i += 1
                continue
            if looks_like_grade(ln):
                break
            if _is_field_line(ln):
                break
            title_parts.append(ln)
            i += 1
        title = " ".join(title_parts).strip()
        if not title:
            i += 1
            continue
        # Next line is AJG 2024 (grade), then up to 9 more. Stop before consuming a field line (next row).
        rest = []
        if i < len(lines):
            rest.append(lines[i].strip())
            i += 1
        while i < len(lines) and len(rest) < 10 and not _is_field_line(lines[i]):
            rest.append(lines[i].strip())
            i += 1
        while len(rest) < 10:
            rest.append("")
        if len(rest) >= 1 and looks_like_grade(rest[0]):
            flush(field, title, rest)
        else:
            # Unrecognized; don't advance past a field line we may have stopped at
            pass

    return rows


def parse_table(text: str) -> list[dict]:
    """
    Parse extracted PDF/text into rows.
    Handles: page breaks, header/footer, multi-line journal titles, tab-separated columns.
    """
    lines = [ln.replace("\r", "").strip() for ln in text.splitlines()]
    rows = []
    i = 0
    current_field = None
    current_title_parts = []

    def flush_row(field: str, title: str, rest_cols: list[str]) -> None:
        """Append one row to rows. rest_cols should be 10 elements."""
        title = title.strip()
        while len(rest_cols) < 10:
            rest_cols.append("")
        rows.append({
            "Field": field,
            "Journal Title": title,
            "AJG 2024": rest_cols[0],
            "AJG 2021": rest_cols[1],
            "Citescore rank": rest_cols[2],
            "SNIP rank": rest_cols[3],
            "SJR rank": rest_cols[4],
            "JIF rank": rest_cols[5],
            "SDG content (2017-21)": rest_cols[6],
            "International co-authorship (2017-21)": rest_cols[7],
            "Academic-non-academic collaborations (2017-21)": rest_cols[8],
            "Citations policy docs (2017-21)": rest_cols[9],
        })

    while i < len(lines):
        line = lines[i]
        # Skip empty, page breaks, and obvious header/footer
        if not line or PAGE_BREAK.match(line):
            i += 1
            continue
        if any(
            line.startswith(x)
            for x in (
                "See discussions",
                "ABS List_Journal",
                "Method ·",
                "CITATIONS",
                "READS",
                "author:",
                "All content following",
                "The user has requested",
            )
        ):
            i += 1
            continue

        m = FIELD_PATTERN.match(line)
        if m:
            field = m.group(1).strip()
            rest = line[m.end() :].strip()
            parts = rest.split("\t")

            if current_field is not None and current_title_parts:
                # Previous row was continuation; we should have flushed when we saw the numeric line.
                # If we didn't, flush with what we have (incomplete row)
                pass

            # Full row on same line: Field \t Title \t AJG24 \t AJG21 \t ... (10 more)
            if len(parts) >= 11 and looks_like_grade(parts[1]):
                title = parts[0]
                rest_cols = [p.strip() for p in parts[1:11]]
                flush_row(field, title, rest_cols)
                current_field = None
                current_title_parts = []
            elif len(parts) >= 2 and looks_like_grade(parts[-10]):
                # 11 parts: title might be parts[0], then 10 columns
                rest_cols = [p.strip() for p in parts[-10:]]
                title = "\t".join(parts[:-10]).strip()
                flush_row(field, title, rest_cols)
                current_field = None
                current_title_parts = []
            else:
                # Title spans multiple lines; rest is start of title
                current_field = field
                current_title_parts = [rest] if rest else []
            i += 1
            continue

        # Continuation line (no field at start)
        if current_field is not None:
            # Could be: more title, or "title_end \t grade \t grade \t ..."
            parts = line.split("\t")
            if len(parts) >= 11 and looks_like_grade(parts[1]):
                # First token is end of title, then 10 columns
                title_end = parts[0].strip()
                rest_cols = [p.strip() for p in parts[1:11]]
                full_title = " ".join(current_title_parts) + " " + title_end if title_end else " ".join(current_title_parts)
                flush_row(current_field, full_title, rest_cols)
                current_field = None
                current_title_parts = []
            else:
                current_title_parts.append(line)
            i += 1
            continue

        # Line that might be trailing part of a split row (numeric line only)
        parts = line.split("\t")
        if len(parts) >= 10 and looks_like_grade(parts[0]):
            # Standalone numeric line (title was on previous line(s)); we don't have field. Skip or treat as missing.
            i += 1
            continue

        i += 1

    if current_field is not None and current_title_parts:
        # Incomplete last row
        flush_row(
            current_field,
            " ".join(current_title_parts),
            ["", "", "", "", "", "", "", "", "", ""],
        )

    return rows


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Digitise AJG 2024 from CABS_AJG_2024.pdf (or extracted text/md)."
    )
    ap.add_argument(
        "input",
        help="Path to CABS_AJG_2024.pdf or to extracted .txt/.md file",
    )
    ap.add_argument(
        "-o",
        "--output",
        default="ajg_2024_ground_truth.csv",
        help="Output CSV path (default: ajg_2024_ground_truth.csv)",
    )
    ap.add_argument(
        "--from-pdf",
        action="store_true",
        help="Force treating input as PDF (default: auto-detect by extension)",
    )
    args = ap.parse_args()

    is_pdf = args.from_pdf or Path(args.input).suffix.lower() == ".pdf"
    try:
        text = read_input(args.input, use_pdf=is_pdf)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # PyMuPDF gives one line per cell; other extractors (e.g. LlamaParse) may give tabs.
    if "\t" in text[:4000] and "ACCOUNT\t" in text[:4000]:
        rows = parse_table(text)
    else:
        rows = parse_table_newline(text)
    if not rows:
        print("Warning: no table rows parsed. Check input format.", file=sys.stderr)

    fieldnames = [
        "Field",
        "Journal Title",
        "AJG 2024",
        "AJG 2021",
        "Citescore rank",
        "SNIP rank",
        "SJR rank",
        "JIF rank",
        "SDG content (2017-21)",
        "International co-authorship (2017-21)",
        "Academic-non-academic collaborations (2017-21)",
        "Citations policy docs (2017-21)",
    ]
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
