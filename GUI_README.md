# Journal Lookup GUI + Literature Search

Streamlit app to browse the AJG 2024 master and run literature searches in selected journals.

---

## Set up as an app on your MacBook

### Option 1: Double‑click launcher (easiest)

1. **Install dependencies once** (in Terminal):
   ```bash
   cd "/Users/b.quinn1/Library/CloudStorage/Dropbox/Documents/journal_quality"
   pip install -r requirements_gui.txt
   ```
   Or with conda: `conda activate llamaparse` then `pip install streamlit pandas`.

2. **Double‑click** `launch_journal_lookup.command` in Finder (in the `journal_quality` folder).
   - A Terminal window will open and start the app; your browser will open to the app.
   - **Keep the Terminal window open** while you use the app; close it when you’re done to stop the server.

### Option 2: App icon in the Dock (macOS app)

1. Open **Automator** (Spotlight → “Automator”).
2. **File → New** → choose **Application**.
3. In the left sidebar, select **Run Shell Script** and drag it into the workflow.
4. Set “Shell” to **/bin/bash** and paste this (edit the path if your folder is elsewhere):
   ```bash
   cd "/Users/b.quinn1/Library/CloudStorage/Dropbox/Documents/journal_quality"
   export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"
   if command -v conda &>/dev/null && conda env list 2>/dev/null | grep -q "llamaparse"; then
     conda run -n llamaparse streamlit run journal_lookup_app.py
   else
     python3 -m streamlit run journal_lookup_app.py
   fi
   ```
5. **File → Save** → name it e.g. “Journal Lookup” and save to **Applications** (or Desktop).
6. Optional: **Right‑click the new app → Get Info** → drag a custom icon onto the small icon (e.g. a PNG).
7. Drag the app to the Dock. When you open it, Terminal will run in the background and the app will open in your browser.

**Note:** Closing the browser tab does not stop the server. To stop it, either quit Terminal (if it’s visible) or run `pkill -f "streamlit run journal_lookup_app"` in Terminal.

---

## Features

- **Filters:** Field (AJG), AJG 2024, AJG 2021, JCR 2021/2023 quartile, free-text search on journal name.
- **Table:** Filtered journals with key columns (grades, JIF, quartiles, ISSN, Publisher).
- **Literature search:** Pick one or more journals from the filtered list; fetch recent works from **OpenAlex** (no API key). Filter by publication year and limit results per journal.
- **Sanity check references (GenAI):** Validate references against **OpenAlex** (ground truth). Accepts:
  - **Paste:** one reference per line (DOIs are detected; otherwise the line is searched by title).
  - **Upload .txt:** one reference per line.
  - **Upload .bib:** BibTeX file; each entry is looked up by DOI (or by title). The app compares BibTeX journal/year to OpenAlex and flags mismatches. Asking GenAI to output BibTeX is recommended (structured, DOI-friendly); fake entries still show as “Not found” in OpenAlex.

## Install

```bash
cd "/Users/b.quinn1/Library/CloudStorage/Dropbox/Documents/journal_quality"
pip install -r requirements_gui.txt
```

Or use a conda env (e.g. `llamaparse` or `llama-parse-env`):

```bash
conda run -n llamaparse pip install streamlit pandas
```

## Run

```bash
cd "/Users/b.quinn1/Library/CloudStorage/Dropbox/Documents/journal_quality"
streamlit run journal_lookup_app.py
```

The app opens in your browser (default http://localhost:8501).

## Data

- **Master:** `ajg_2024_master_with_jcr.csv` (must exist; generate with `patch_master_with_jcr_metrics.py` if needed).
- **Literature:** OpenAlex (https://openalex.org), public API, no key required. Rate limits apply for heavy use.

## Optional

- **Theme:** Create `.streamlit/config.toml` in this folder to set theme (e.g. dark), or use the app menu (top right) → Settings.
