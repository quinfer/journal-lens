# Digitising the ABS/AJG 2024 list from the PDF

## Ground truth

**CABS_AJG_2024.pdf** is the canonical source for the latest ABS Academic Journal Guide (AJG) 2024 list. All downstream data (CSV, merged JCR tables, tools) should be derived from or validated against this PDF.

## Do you need LlamaParse?

**Not necessarily.** It depends how the PDF is consumed:

| Approach | Pros | Cons |
|----------|-----|-----|
| **Local PDF extraction** (e.g. PyMuPDF, pdfplumber) | No API key, free, fast, works offline. Your PDF has a clear text layer and tab-separated table body. | Layout may vary by viewer; multi-line journal titles need careful parsing. |
| **LlamaParse** (TickLab repo: `/Users/b.quinn1/Documents/TickLab/llama-parse`) | Layout-aware extraction; can produce cleaner markdown/tables; good for complex or image-heavy PDFs. | Requires `LLAMA_CLOUD_API_KEY` and (optionally) `llama-parse` conda env. |

**Recommendation:** Try the local extractor first (script below). If the resulting CSV is missing rows or has mangled columns (e.g. multi-line titles broken wrong), run LlamaParse on the PDF and point the same table parser at the generated markdown.

## Workflow

1. **Extract** PDF → text or markdown (local script or LlamaParse).
2. **Parse** text/markdown → one row per journal (field, title, AJG 2024, AJG 2021, ranks, %s).
3. **Output** a single ground-truth CSV (e.g. `ajg_2024_ground_truth.csv`) in this folder.
4. Use that CSV as the master list for merging with JCR and for any tools (lookup, filters, exports).

## Conda envs you can use

You have two conda envs with LlamaParse (and now **pymupdf** in both):

| Env               | LlamaParse | PyMuPDF |
|-------------------|------------|---------|
| `llama-parse-env` | ✓          | ✓       |
| `llamaparse`      | ✓          | ✓       |

Use either for running the digitization script or the TickLab LlamaParse scripts.

## Using the TickLab LlamaParse scripts

From the llama-parse directory (use either env):

```bash
cd /Users/b.quinn1/Documents/TickLab/llama-parse
# Set LLAMA_CLOUD_API_KEY in .env or environment
conda run -n llama-parse-env python parse_llamaparse.py "/Users/b.quinn1/Library/CloudStorage/Dropbox/Documents/journal_quality/CABS_AJG_2024.pdf" --format markdown
# or: conda run -n llamaparse python parse_llamaparse.py "..." --format markdown
```

This writes `CABS_AJG_2024.md` next to the PDF. Then run the digitization script (see below) on that `.md` file.

## Script provided

- **`digitize_ajg2024_from_pdf.py`** – Extracts text from the PDF (local, via PyMuPDF) or accepts pre-extracted text/markdown, parses table rows (handles page breaks and both tab- and newline-separated layout), and writes `ajg_2024_ground_truth.csv`. Run from the `journal_quality` directory; see script docstring and `--help`.

  **Dependency:** `pymupdf` for PDF extraction. Either install in your current env (`pip install pymupdf`) or use a conda env that has it: `llama-parse-env` or `llamaparse` (both now include pymupdf).

  **Note:** Local PDF extraction (PyMuPDF) yields one line per cell; a few journal titles that span two lines in the PDF can end up as separate rows (e.g. “Evaluation” alone). For maximum fidelity and to fix those edge cases, run LlamaParse first and pass the generated markdown to this script.
