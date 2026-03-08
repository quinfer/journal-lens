# Journal Quality & Literature

A small toolkit for working with the **ABS Academic Journal Guide (AJG) 2024** and related metrics: browse journals by field and grade, search recent literature via **OpenAlex**, and **sanity-check references** (e.g. from GenAI) against OpenAlex as ground truth.

---

## Features

| Feature | Description |
|--------|-------------|
| **Journal lookup** | Filter the AJG 2024 master by Field, AJG grade, JCR quartile; search by journal name. |
| **Literature search** | Fetch recent articles from selected journals via OpenAlex (no API key). Optional filters: text search, open access, date range, sort by newest or most cited. |
| **Reference sanity check** | Paste or upload references (plain text or BibTeX); validate each against OpenAlex and report Found / Not found, journal in AJG master, and mismatches (e.g. year or journal). |

---

## Quick start

**Requirements:** Python 3.9+, Streamlit, pandas.

```bash
git clone https://github.com/quinfer/journal-lens.git
cd journal-lens
pip install -r requirements.txt
streamlit run journal_lookup_app.py
```

The app opens at `http://localhost:8501`. It expects **`ajg_2024_master_with_jcr.csv`** in the project root; the repo includes the required CSVs so it runs out of the box (see [Data pipeline](#data-pipeline) to rebuild from sources).

---

## Project structure

```
journal_quality/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── Procfile                  # Railway (and similar) deploy: streamlit on $PORT
├── journal_lookup_app.py     # Streamlit app (lookup + literature + sanity check)
├── launch_journal_lookup.command   # Optional: double-click launcher (macOS)
│
├── Data pipeline (build master from sources)
├── digitize_ajg2024_from_pdf.py    # PDF → ground-truth CSV (AJG 2024)
├── patch_master_with_jcr_metrics.py # Merge JCR/ABS metrics into master
│
├── ajg_2024_ground_truth.csv       # Output of digitize (from PDF)
├── ajg_2024_master_with_jcr.csv    # Patched master (app data source)
├── JCR_ABS.csv, BarryQuinn_JCR_*.csv  # JCR/ABS inputs for patch
│
├── docs/                     # Detailed guides
│   ├── DIGITIZE.md           # PDF digitization (LlamaParse optional)
│   ├── GUI.md                # App install, run, macOS setup
│   ├── MASTER_WITH_JCR.md    # Patched master columns and build
│   ├── OPENALEX_SEARCH.md    # OpenAlex filter/search reference
│   └── RED_TEAM_REPORT.md    # Digitization validation notes
│
└── .streamlit/
    └── config.toml           # Streamlit theme (optional)
```

---

## Data pipeline

1. **Ground truth:** `CABS_AJG_2024.pdf` (official ABS list) → **`digitize_ajg2024_from_pdf.py`** → `ajg_2024_ground_truth.csv`.
2. **Enrich:** Run **`patch_master_with_jcr_metrics.py`** to merge in JCR 2021/2023 metrics (from `JCR_ABS.csv` and `BarryQuinn_JCR_*.csv`) → **`ajg_2024_master_with_jcr.csv`**.
3. The **app** reads `ajg_2024_master_with_jcr.csv`. If you only have the PDF and JCR exports, run the two scripts in order; see `docs/DIGITIZE.md` and `docs/MASTER_WITH_JCR.md`.

---

## Deploy (Railway)

To run the app on Railway and get a public URL, see **[docs/DEPLOY_RAILWAY.md](docs/DEPLOY_RAILWAY.md)**. You need the repo on GitHub and `ajg_2024_master_with_jcr.csv` committed (or otherwise available at build/runtime).

---

## Documentation

- **[docs/GUI.md](docs/GUI.md)** — Install, run, and (optional) macOS app setup.
- **[docs/DIGITIZE.md](docs/DIGITIZE.md)** — Digitizing the PDF (local or LlamaParse).
- **[docs/MASTER_WITH_JCR.md](docs/MASTER_WITH_JCR.md)** — Patched master columns and how to rebuild.
- **[docs/OPENALEX_SEARCH.md](docs/OPENALEX_SEARCH.md)** — OpenAlex filters and search options for the literature feature.
- **[docs/RED_TEAM_REPORT.md](docs/RED_TEAM_REPORT.md)** — Notes on digitization validation.

---

## License

Use and adapt as you like. If you redistribute, attribution and a link to the repo are appreciated.
