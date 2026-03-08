# Digitising the AJG 2024 list from the PDF

**CABS_AJG_2024.pdf** is the canonical source. All downstream CSVs and the app’s master list should be derived from or validated against this PDF.

## Do you need LlamaParse?

| Approach | Pros | Cons |
|----------|------|------|
| **Local (PyMuPDF)** | No API key, fast, offline. | Multi-line titles in the PDF can occasionally become separate rows. |
| **LlamaParse** | Layout-aware; can improve table extraction. | Requires `LLAMA_CLOUD_API_KEY`. |

**Recommendation:** Run the local script first. If rows are missing or titles are split, try LlamaParse and pass the generated markdown to the same script.

## Workflow

1. **Extract** PDF → text (or markdown via LlamaParse).
2. **Parse** with **`digitize_ajg2024_from_pdf.py`** → one row per journal.
3. **Output** `ajg_2024_ground_truth.csv`.
4. Run **`patch_master_with_jcr_metrics.py`** to build the app’s master file (see [MASTER_WITH_JCR.md](MASTER_WITH_JCR.md)).

## Run the digitization script

```bash
# From the project root; requires pymupdf
pip install pymupdf
python digitize_ajg2024_from_pdf.py CABS_AJG_2024.pdf -o ajg_2024_ground_truth.csv
```

To use pre-extracted markdown (e.g. from LlamaParse):

```bash
python digitize_ajg2024_from_pdf.py CABS_AJG_2024.md -o ajg_2024_ground_truth.csv
```

See script `--help` for options. A few edge-case titles (e.g. “Evaluation” as a fragment) may appear as separate rows; these can be cleaned manually or by re-running with LlamaParse output.
