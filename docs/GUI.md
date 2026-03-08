# Journal Lookup app — Install & run

Streamlit app for browsing the AJG 2024 master, searching literature via OpenAlex, and validating references.

## Install

```bash
cd journal_quality
pip install -r requirements.txt
```

Or with conda: `conda activate your_env` then `pip install streamlit pandas`.

## Run

```bash
streamlit run journal_lookup_app.py
```

The app opens at http://localhost:8501. It reads **`ajg_2024_master_with_jcr.csv`** from the project root (create it with the data pipeline; see [MASTER_WITH_JCR.md](MASTER_WITH_JCR.md)).

## Features

- **Filters:** Field (AJG), AJG 2024/2021, JCR 2021/2023 quartile, free-text search on journal name.
- **Table:** Filtered journals with grades, JIF, quartiles, ISSN, Publisher.
- **Literature search:** Select journals; fetch works from OpenAlex (no API key). Optional: text search, open access only, date range, sort by newest or most cited.
- **Reference sanity check:** Paste or upload .txt / .bib; validate against OpenAlex; report Found / Not found, journal in AJG master, and mismatches (e.g. BibTeX vs OpenAlex year/journal).

## macOS: run as an app

**Option 1 — Double-click:** Use **`launch_journal_lookup.command`** in the project folder (keep the Terminal window open while using the app).

**Option 2 — Dock icon:** In Automator, create an Application that runs a shell script: `cd /path/to/journal_quality && streamlit run journal_lookup_app.py`. Save to Applications and drag to the Dock.

To stop the server: close the Terminal or run `pkill -f "streamlit run journal_lookup_app"`.

## Theme

Edit **`.streamlit/config.toml`** in the project to change theme (e.g. dark). Or use the app menu (top right) → Settings.
