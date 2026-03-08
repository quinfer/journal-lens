# Deploy Journal Lookup to Railway

Deploy the Streamlit app so it runs on Railway and is reachable via a public URL.

---

## Prerequisites

- **GitHub repo** with this project (including `Procfile` and `requirements.txt`).
- **Master CSV in the repo:** The app reads `ajg_2024_master_with_jcr.csv` from the project root. Either:
  - Commit `ajg_2024_master_with_jcr.csv` (ensure it’s not in `.gitignore`), or
  - Build it in a deploy step or provide it via a volume (advanced).

---

## Steps

1. **Sign in:** [railway.app](https://railway.app) → sign in with GitHub.

2. **New project:** **New Project** → **Deploy from GitHub repo** → select your `journal_quality` repo (or fork). Railway will clone and build.

3. **Build:** Railway uses the repo’s `requirements.txt` and runs the **Procfile** command:
   ```text
   web: streamlit run journal_lookup_app.py --server.port=$PORT --server.address=0.0.0.0
   ```
   This makes Streamlit listen on Railway’s `PORT` and on all interfaces so the proxy can reach it.

4. **Public URL:** In the project, open your service → **Settings** → **Networking** → **Generate domain**. Use the generated URL (e.g. `https://your-app.up.railway.app`) to open the app.

5. **Optional – root URL:** If you want the app at the root path (e.g. `https://your-app.up.railway.app/`), no extra config is needed; Streamlit serves the app at `/`.

---

## If the app fails to start

- **“Master CSV not found”:** Ensure `ajg_2024_master_with_jcr.csv` is in the repo root and not ignored by `.gitignore`. If you excluded `*.csv`, add an exception for this file or commit it.
- **Port / connection:** The Procfile already uses `$PORT` and `--server.address=0.0.0.0`; don’t override the start command with a fixed port.
- **Build errors:** Check the build logs; Railway runs `pip install -r requirements.txt`. Fix any missing or conflicting dependencies in `requirements.txt`.

---

## Cost

Railway has a free tier with a monthly allowance; beyond that it’s pay-as-you-go. See [Railway pricing](https://railway.app/pricing).
