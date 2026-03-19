# Provenance (journal lookup app) — Install & run

Streamlit app **Provenance** for browsing the AJG 2024 master, finding papers in those journals (OpenAlex), and checking references (.bib or pasted text) against OpenAlex and the AJG list. See the in-app expander *Why “Provenance”?* for the student-facing explanation.

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

- **Journal list filters:** Field (AJG), AJG 2024/2021, JCR quartiles, free-text search on journal name.
- **Journal directory:** Filtered table with grades, JIF, quartiles, ISSN, publisher.
- **Find papers in these journals:** Select journals (ISSN required); fetch works from OpenAlex. Optional keywords, open access, year range, sort.
- **Check your references:** Paste or upload `.txt` / `.bib`; match against OpenAlex; optional download of a cleaned `.bib` for matched items.

## macOS: run as an app

**Option 1 — Double-click:** Use **`launch_journal_lookup.command`** in the project folder (keep the Terminal window open while using the app).

**Option 2 — Dock icon:** In Automator, create an Application that runs a shell script: `cd /path/to/journal_quality && streamlit run journal_lookup_app.py`. Save to Applications and drag to the Dock.

To stop the server: close the Terminal or run `pkill -f "streamlit run journal_lookup_app"`.

## Theme

Edit **`.streamlit/config.toml`** in the project to change theme (e.g. dark). Or use the app menu (top right) → Settings.
