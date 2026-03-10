"""
Journal Lookup GUI + Literature Search

- Browse and filter the AJG 2024 master by Field, grade, JCR quartile, etc.
- Search by journal name.
- Literature search: find recent works in selected/filtered journals via OpenAlex (no API key).
- Sanity check: validate references (e.g. from GenAI) against OpenAlex + AJG master.

Run: streamlit run journal_lookup_app.py
"""

import io
import re
import urllib.parse
import urllib.request
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import streamlit as st

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parent
MASTER_CSV = DATA_DIR / "ajg_2024_master_with_jcr.csv"

# -----------------------------------------------------------------------------
# Load data
# -----------------------------------------------------------------------------
@st.cache_data
def load_master():
    if not MASTER_CSV.exists():
        return None
    df = pd.read_csv(MASTER_CSV)
    # Coerce numeric-ish columns for display
    for c in ["Citescore rank", "SNIP rank", "SJR rank", "JIF rank", "JCR_2021_JIF", "JCR_2023_JIF"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def format_issn(issn: str) -> str:
    """Turn 8-char ISSN (digits or 7 digits + X) into XXXX-XXXX format for display/API."""
    if not issn or not isinstance(issn, str):
        return ""
    s = str(issn).strip().upper().replace("-", "")
    # Allow digits and trailing X (valid ISSN check digit)
    s = "".join(c for c in s if c in "0123456789X")
    if len(s) == 8:
        return f"{s[:4]}-{s[4:]}"
    return s


# -----------------------------------------------------------------------------
# OpenAlex literature search (no API key required)
# -----------------------------------------------------------------------------
def openalex_works_for_issn(
    issn: str,
    per_page: int = 25,
    from_year: int | None = None,
    to_year: int | None = None,
    search_query: str | None = None,
    open_access_only: bool = False,
    sort_by: str = "publication_date:desc",
) -> list[dict]:
    """Fetch works from OpenAlex for a journal by ISSN, with optional search and filters."""
    import urllib.parse
    import urllib.request

    issn_fmt = format_issn(issn)
    if not issn_fmt or len(issn_fmt) < 8:
        return []

    filters = [f"primary_location.source.issn:{issn_fmt}"]
    if from_year is not None:
        filters.append(f"from_publication_date:{from_year}-01-01")
    if to_year is not None:
        filters.append(f"to_publication_date:{to_year}-12-31")
    if open_access_only:
        filters.append("is_oa:true")

    params = {
        "filter": ",".join(filters),
        "per-page": min(per_page, 200),
        "sort": sort_by,
    }
    if search_query and search_query.strip():
        params["search"] = search_query.strip()
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "JournalLookupApp/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read().decode()
    except Exception:
        return []
    try:
        import json
        out = json.loads(data)
        return out.get("results") or []
    except Exception:
        return []


def get_oa_pdf_url(work: dict) -> str | None:
    """Return a URL for the open-access version (PDF or landing page), or None."""
    oa = work.get("open_access") or {}
    url = oa.get("oa_url")
    if url and isinstance(url, str) and url.startswith("http"):
        return url
    loc = work.get("best_oa_location") or work.get("primary_location") or {}
    url = loc.get("pdf_url") or loc.get("landing_page_url")
    if url and isinstance(url, str) and url.startswith("http"):
        return url
    for loc in work.get("locations") or []:
        if loc.get("is_oa"):
            url = loc.get("pdf_url") or loc.get("landing_page_url")
            if url and isinstance(url, str) and url.startswith("http"):
                return url
    return None


def fetch_url_as_bytes(url: str, timeout: int = 20, max_size: int = 25 * 1024 * 1024) -> tuple[bytes | None, str]:
    """Fetch URL; return (body or None, extension 'pdf' or 'html'). Follows redirects."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/pdf,text/html,application/xhtml+xml,*/*;q=0.8",
            },
        )
        opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
        with opener.open(req, timeout=timeout) as resp:
            ct = (resp.headers.get("Content-Type") or "").lower()
            data = resp.read(max_size + 1)
            if len(data) > max_size:
                return None, "html"
            ext = "pdf" if "pdf" in ct else "html"
            return bytes(data), ext
    except Exception:
        return None, "html"


def safe_filename(title: str, max_len: int = 80) -> str:
    """Make a safe filename from a title."""
    s = re.sub(r"[^\w\s\-\.]", "", title)[:max_len].strip() or "paper"
    return re.sub(r"\s+", "_", s)


def works_to_display(works: list[dict], include_journal: bool = False) -> list[dict]:
    """Convert OpenAlex work objects to simple rows for display."""
    rows = []
    for w in works:
        title = w.get("display_name") or w.get("title") or ""
        year = (w.get("publication_date") or "")[:4] or ""
        authors = w.get("authorships") or []
        author_names = ", ".join(
            (a.get("author", {}).get("display_name") or "") for a in authors[:5]
        )
        if len(authors) > 5:
            author_names += " et al."
        ids = w.get("ids") or {}
        doi = (ids.get("doi") or "").replace("https://doi.org/", "")
        oa = w.get("open_access") or {}
        is_oa = oa.get("is_oa", False)
        url = w.get("id") or (f"https://doi.org/{doi}" if doi else "")
        if isinstance(url, str) and url.startswith("https://doi.org/"):
            pass
        elif isinstance(url, str) and not url.startswith("http"):
            url = f"https://doi.org/{url}" if url else ""
        cited = w.get("cited_by_count") or 0
        pdf_url = get_oa_pdf_url(w)
        row = {
            "Title": title,
            "Year": year,
            "Authors": author_names,
            "Cited by": cited,
            "DOI": doi,
            "Open access": "Yes" if is_oa else "No",
            "PDF": pdf_url or "",
            "URL": url,
        }
        if include_journal:
            row["Journal"] = w.get("_journal", "")
        rows.append(row)
    return rows


# -----------------------------------------------------------------------------
# OpenAlex lookup by DOI or search (for reference validation)
# -----------------------------------------------------------------------------
DOI_PATTERN = re.compile(
    r"(?:https?://(?:dx\.)?doi\.org/|DOI:?\s*)(10\.\d{4,}/[^\s\]>\)]+)",
    re.IGNORECASE,
)


def extract_doi(line: str) -> str | None:
    """Extract first DOI from a line of text."""
    m = DOI_PATTERN.search(line)
    if m:
        return m.group(1).rstrip(".,;:)")
    return None


def openalex_work_by_doi(doi: str) -> dict | None:
    """Fetch a single work from OpenAlex by DOI. Returns work dict or None."""
    doi = doi.strip().rstrip(".,;:)")
    if not doi.startswith("http"):
        doi = f"https://doi.org/{doi}"
    params = {"filter": f"doi:{doi}", "per-page": 1}
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "JournalLookupApp/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode()
    except Exception:
        return None
    try:
        import json
        out = json.loads(data)
        results = out.get("results") or []
        return results[0] if results else None
    except Exception:
        return None


def openalex_work_by_search(query: str, per_page: int = 3) -> list[dict]:
    """Search OpenAlex works by title/abstract; return list of results."""
    if not query or len(query.strip()) < 3:
        return []
    params = {"search": query.strip()[:200], "per-page": per_page, "sort": "relevance_score:desc"}
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "JournalLookupApp/1.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = resp.read().decode()
    except Exception:
        return []
    try:
        import json
        out = json.loads(data)
        return out.get("results") or []
    except Exception:
        return []


def _first_str(val) -> str:
    """Normalize ISSN field: OpenAlex may return a string or a list of strings."""
    if val is None:
        return ""
    if isinstance(val, list):
        for item in val:
            if isinstance(item, str) and item.strip():
                return item.strip()
        return ""
    return str(val).strip() if val else ""


def get_journal_from_work(w: dict) -> tuple[str, str]:
    """From OpenAlex work get (journal display name, ISSN)."""
    loc = w.get("primary_location") or {}
    src = loc.get("source") or {}
    name = src.get("display_name") or ""
    issn = _first_str(src.get("issn"))
    if not issn:
        issn = _first_str(src.get("issn_l"))
    return name, issn


def normalize_title_for_match(s: str) -> str:
    """Lowercase, collapse spaces, remove punctuation for fuzzy match."""
    if not s:
        return ""
    s = re.sub(r"[^\w\s]", " ", str(s).lower())
    return " ".join(s.split())


def parse_bibtex_string(bib_content: str) -> list[dict]:
    """Parse .bib content into list of dicts with keys doi, title, journal, year, snippet, entry_type, raw_block. No external deps."""
    entries = []
    # Find each @type{ and capture type and block until next @
    for m in re.finditer(r"@(\w+)\s*\{", bib_content, re.IGNORECASE):
        entry_type = m.group(1)
        start = m.end()
        next_m = re.search(r"@\w+\s*\{", bib_content[start:], re.IGNORECASE)
        end = start + next_m.start() if next_m else len(bib_content)
        block = bib_content[start:end]
        field_part = block
        # Extract key = value or key = {value} or key = "value"
        def get_field(name: str) -> str:
            # Quoted value: name = "value"
            quoted = re.search(
                rf"{re.escape(name)}\s*=\s*[\"]([^\"]+)[\"]",
                field_part,
                re.IGNORECASE | re.DOTALL,
            )
            if quoted:
                return quoted.group(1).strip().replace("\n", " ")
            # Braced value: name = { ... } (allow nested braces like {C}ox)
            braced = re.search(rf"{re.escape(name)}\s*=\s*[\{{]\s*", field_part, re.IGNORECASE)
            if braced:
                start_b = braced.end()
                depth = 1
                i = start_b
                while i < len(field_part) and depth > 0:
                    if field_part[i] == "{":
                        depth += 1
                    elif field_part[i] == "}":
                        depth -= 1
                    i += 1
                if depth == 0:
                    return field_part[start_b : i - 1].strip().replace("\n", " ")
            # Fallback: non-nested { ... } only
            simple = re.compile(
                rf"{re.escape(name)}\s*=\s*[\{{]\s*([^{{}}]+)[\}}]",
                re.IGNORECASE | re.DOTALL,
            )
            m_s = simple.search(field_part)
            if m_s:
                return (m_s.group(1) or "").strip().replace("\n", " ")
            return ""
        doi = get_field("doi") or get_field("DOI")
        if not doi and "doi.org" in field_part:
            m_doi = re.search(r"doi\.org/(10\.\d{4,}/[^\s\}\"]+)", field_part)
            if m_doi:
                doi = m_doi.group(1).rstrip(".,;:)")
        title = get_field("title") or get_field("Title")
        journal = get_field("journal") or get_field("Journal") or get_field("journaltitle")
        year = get_field("year") or get_field("Year")
        snippet = (title or journal or doi or field_part[:60]).strip()[:80]
        entries.append({
            "doi": doi or None,
            "title": title,
            "journal": journal,
            "year": year,
            "snippet": snippet,
            "entry_type": entry_type,
            "raw_block": block,
        })
    return entries


def _replace_bibtex_field(block: str, field: str, new_value: str) -> str:
    """Replace first occurrence of field = { ... } or field = \"...\" in block with field = { new_value }."""
    if not new_value:
        return block
    # Braced: field = { ... } (brace-counted)
    braced = re.search(rf"({re.escape(field)}\s*=\s*[\{{])\s*", block, re.IGNORECASE)
    if braced:
        start = braced.end()
        depth = 1
        i = start
        while i < len(block) and depth > 0:
            if block[i] == "{":
                depth += 1
            elif block[i] == "}":
                depth -= 1
            i += 1
        if depth == 0:
            return block[:start] + new_value + block[i - 1:]
    # Quoted: field = " ... "
    quoted = re.search(rf"({re.escape(field)}\s*=\s*[\"])([^\"]*)([\"])", block, re.IGNORECASE)
    if quoted:
        return block[: quoted.end(1)] + new_value + block[quoted.start(3) :]
    return block


def build_corrected_bibtex(results: list[dict], refs_raw: list) -> str:
    """Build a .bib string containing only Found entries with year/journal/title from OpenAlex where we have them."""
    lines = []
    for i, r in enumerate(results):
        if r.get("Status") != "Found":
            continue
        ref = refs_raw[i] if i < len(refs_raw) else None
        if not isinstance(ref, dict) or "raw_block" not in ref:
            continue
        block = ref["raw_block"]
        entry_type = ref.get("entry_type", "article")
        oa_year = (r.get("Year") or "").strip()
        oa_journal = (r.get("_oa_journal_full") or r.get("Journal (OpenAlex)") or "").strip()
        oa_title = (r.get("_oa_title_full") or "").strip()
        if oa_year:
            block = _replace_bibtex_field(block, "year", oa_year)
        if oa_journal:
            block = _replace_bibtex_field(block, "journal", oa_journal)
            block = _replace_bibtex_field(block, "journaltitle", oa_journal)
        if oa_title:
            block = _replace_bibtex_field(block, "title", oa_title)
        lines.append(f"@{entry_type}{{{block}\n")
    return "\n".join(lines) if lines else ""


def find_journal_in_master(master_df: pd.DataFrame, journal_name: str, issn: str) -> pd.Series | None:
    """Return first master row matching journal by name or ISSN, else None."""
    if not journal_name and not issn:
        return None
    issn_clean = re.sub(r"\D", "", str(issn)) if issn else ""
    if issn_clean and len(issn_clean) >= 7:
        master_issn = master_df["ISSN"].astype(str).str.replace(r"\D", "", regex=True)
        match = master_df[master_issn == issn_clean]
        if not match.empty:
            return match.iloc[0]
    name_norm = normalize_title_for_match(journal_name)
    if not name_norm:
        return None
    for _, row in master_df.iterrows():
        t = (row.get("Journal Title") or "")
        if name_norm in normalize_title_for_match(t) or normalize_title_for_match(t) in name_norm:
            return row
    return None


# -----------------------------------------------------------------------------
# UI
# -----------------------------------------------------------------------------
def main():
    st.set_page_config(
        page_title="Journal Lookup & Literature",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    # Light polish: reduce top padding, subtle divider
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
        footer { visibility: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("Journal Lookup & Literature")
    st.caption(
        "Browse AJG 2024 by field and grade • Search recent literature via OpenAlex • Validate references (e.g. from GenAI) against OpenAlex and the AJG master."
    )

    df = load_master()
    if df is None:
        st.error(f"Master CSV not found: {MASTER_CSV}")
        return

    # ---- Sidebar filters ----
    st.sidebar.header("Filters")
    field_vals = sorted(df["Field"].dropna().astype(str).unique().tolist())
    field_filter = st.sidebar.multiselect("Field (AJG)", field_vals, default=[])
    ajg24_vals = sorted(df["AJG 2024"].dropna().astype(str).unique().tolist(), key=lambda x: (x.replace("*", ""), x))
    ajg24_filter = st.sidebar.multiselect("AJG 2024", ajg24_vals, default=[])
    ajg21_filter = st.sidebar.multiselect("AJG 2021", sorted(df["AJG 2021"].dropna().astype(str).unique().tolist(), key=lambda x: (x.replace("*", ""), x)), default=[])
    q_vals = ["Q1", "Q2", "Q3", "Q4"]
    q2021 = st.sidebar.multiselect("JCR 2021 quartile", q_vals, default=[])
    q2023 = st.sidebar.multiselect("JCR 2023 quartile", q_vals, default=[])
    title_search = st.sidebar.text_input("Search journal name", placeholder="e.g. Accounting Review")

    # Apply filters
    subset = df.copy()
    if field_filter:
        subset = subset[subset["Field"].astype(str).isin(field_filter)]
    if ajg24_filter:
        subset = subset[subset["AJG 2024"].astype(str).isin(ajg24_filter)]
    if ajg21_filter:
        subset = subset[subset["AJG 2021"].astype(str).isin(ajg21_filter)]
    if q2021:
        subset = subset[subset["JCR_2021_JIF_Quartile"].astype(str).isin(q2021)]
    if q2023:
        subset = subset[subset["JCR_2023_JIF_Quartile"].astype(str).isin(q2023)]
    if title_search:
        subset = subset[
            subset["Journal Title"].astype(str).str.lower().str.contains(title_search.lower(), na=False)
        ]

    st.sidebar.metric("Journals matching filters", len(subset))

    # ---- Main: data table ----
    st.header("Journals")
    display_cols = [
        "Field", "Journal Title", "AJG 2024", "AJG 2021",
        "JCR_2021_JIF_Quartile", "JCR_2023_JIF_Quartile",
        "JCR_2021_JIF", "JCR_2023_JIF", "ISSN", "Publisher",
    ]
    display_cols = [c for c in display_cols if c in subset.columns]
    st.dataframe(
        subset[display_cols].head(500),
        use_container_width=True,
        hide_index=True,
    )
    if len(subset) > 500:
        st.caption(f"Showing first 500 of {len(subset)}. Narrow filters to see fewer.")

    # ---- Literature search tab ----
    st.divider()
    st.subheader("Literature search (OpenAlex)")
    st.caption("Fetch articles for selected journals (by ISSN). Optional: text search, open access only, date range, sort by newest or most cited. See docs/OPENALEX_SEARCH.md for full filter reference.")

    # Journals with ISSN for literature search (ISSN can be 8 digits or 7 digits + X)
    def valid_issn(s):
        if pd.isna(s) or not str(s).strip():
            return False
        s = str(s).strip().upper().replace("-", "")
        if len(s) == 8 and (s[-1] in "X0123456789" and s[:-1].isdigit()):
            return True
        if len(s) == 8 and s.isdigit():
            return True
        return False
    with_issn = subset[subset["ISSN"].apply(valid_issn)]
    if with_issn.empty:
        st.info("No journals with ISSN in the current selection. Remove some filters or pick a different set.")
    else:
        lit_journals = st.multiselect(
            "Journals to search (select one or more)",
            options=with_issn["Journal Title"].astype(str).tolist(),
            default=with_issn["Journal Title"].astype(str).iloc[:1].tolist() if len(with_issn) else [],
            max_selections=5,
        )
        from_year = st.number_input("From publication year", min_value=1990, max_value=2030, value=2020, step=1)
        to_year = st.number_input("To publication year (optional)", min_value=1990, max_value=2030, value=2030, step=1, help="Leave at 2030 for 'up to now'")
        search_query = st.text_input("Search in title/abstract (optional)", placeholder="e.g. corporate governance")
        open_access_only = st.checkbox("Open access only", value=False)
        sort_by = st.selectbox(
            "Sort by",
            options=["publication_date:desc", "cited_by_count:desc"],
            format_func=lambda x: "Newest first" if x == "publication_date:desc" else "Most cited first",
            index=0,
        )
        per_journal = st.slider("Max works per journal", 5, 50, 15)
        if st.button("Search literature"):
            all_works = []
            issn_to_title = with_issn.set_index("Journal Title")["ISSN"].to_dict()
            for title in lit_journals:
                issn = issn_to_title.get(title, "")
                if not str(issn).strip():
                    continue
                with st.spinner(f"Fetching works for {title[:50]}..."):
                    works = openalex_works_for_issn(
                        str(issn),
                        per_page=per_journal,
                        from_year=from_year,
                        to_year=to_year if to_year != 2030 else None,
                        search_query=search_query.strip() or None,
                        open_access_only=open_access_only,
                        sort_by=sort_by,
                    )
                for w in works:
                    w["_journal"] = title
                all_works.extend(works)
            if not all_works:
                st.warning("No works returned. Try different journals or a later from-year.")
            else:
                rows = works_to_display(all_works, include_journal=len(lit_journals) > 1)
                st.session_state["literature_works"] = all_works
                st.session_state["literature_rows"] = rows
                st.session_state.pop("literature_zip_bytes", None)
                st.session_state.pop("literature_zip_fetched", None)
                st.session_state.pop("literature_zip_total", None)
                st.dataframe(
                    pd.DataFrame(rows),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "URL": st.column_config.LinkColumn("URL", display_text="Link"),
                        "PDF": st.column_config.LinkColumn("PDF", display_text="PDF"),
                    },
                )
                st.success(f"Found {len(rows)} works.")

        # ---- Download papers (bulk or selected) ----
        if st.session_state.get("literature_works"):
            works = st.session_state["literature_works"]
            works_with_pdf = [(w, get_oa_pdf_url(w)) for w in works if get_oa_pdf_url(w)]
            if works_with_pdf:
                st.markdown("**Download open-access papers**")
                export_df = pd.DataFrame([
                    {
                        "Title": (w.get("display_name") or "")[:200],
                        "Year": (w.get("publication_date") or "")[:4],
                        "DOI": (w.get("ids") or {}).get("doi", "").replace("https://doi.org/", ""),
                        "PDF_URL": get_oa_pdf_url(w),
                    }
                    for w in works
                    if get_oa_pdf_url(w)
                ])
                st.download_button(
                    "Export all OA/PDF links (CSV)",
                    data=export_df.to_csv(index=False),
                    mime="text/csv",
                    file_name="journal_lens_oa_links.csv",
                    help="CSV of titles and PDF/landing-page URLs for use in a download manager or browser.",
                )
                st.caption("Or select papers below to download as a ZIP (max 15).")
                max_download = min(15, len(works_with_pdf))
                options = list(range(len(works_with_pdf)))
                labels = [
                    f"{works_with_pdf[i][0].get('display_name', '')[:55]} ({(works_with_pdf[i][0].get('publication_date') or '')[:4]})"
                    for i in options
                ]
                selected_idx = st.multiselect(
                    "Select papers to include in ZIP",
                    options=options,
                    format_func=lambda i: labels[i],
                    default=options[:min(3, len(options))],
                    max_selections=max_download,
                )
                if st.button("Create ZIP of selected papers"):
                    if not selected_idx:
                        st.warning("Select at least one paper.")
                    else:
                        with st.spinner("Fetching papers..."):
                            buf = io.BytesIO()
                            fetched_count = 0
                            with ZipFile(buf, "w") as zf:
                                for i in selected_idx:
                                    w, pdf_url = works_with_pdf[i]
                                    title = w.get("display_name") or "paper"
                                    year = (w.get("publication_date") or "")[:4]
                                    body, ext = fetch_url_as_bytes(pdf_url)
                                    if body:
                                        name = f"{safe_filename(title)}_{year}.{ext}"
                                        zf.writestr(name, body)
                                        fetched_count += 1
                                    else:
                                        # Always add something: a link file so the ZIP isn't empty
                                        link_content = f"{title}\n\nYear: {year}\n\nOpen in browser:\n{pdf_url}\n"
                                        name = f"{safe_filename(title)}_{year}_link.txt"
                                        zf.writestr(name, link_content.encode("utf-8"))
                            buf.seek(0)
                            st.session_state["literature_zip_bytes"] = buf.getvalue()
                            st.session_state["literature_zip_fetched"] = fetched_count
                            st.session_state["literature_zip_total"] = len(selected_idx)
                if st.session_state.get("literature_zip_bytes"):
                    total = st.session_state.get("literature_zip_total", 0)
                    fetched = st.session_state.get("literature_zip_fetched", 0)
                    st.download_button(
                        "Download ZIP",
                        data=st.session_state["literature_zip_bytes"],
                        mime="application/zip",
                        file_name="journal_lens_papers.zip",
                        key="dl_zip",
                    )
                    if fetched < total:
                        st.info(f"ZIP has {fetched} fetched file(s) (PDF/HTML) and {total - fetched} link-only file(s). Open the .txt files in the ZIP to get the URL and download in your browser if needed.")
                    else:
                        st.caption("ZIP contains the selected papers (PDF or HTML). Generate again to change selection.")
            else:
                st.caption("No open-access PDF/landing URLs in this result set. Try “Open access only” in the search filters.")

    # ---- Sanity check references (GenAI) ----
    st.divider()
    st.subheader("Sanity check references (GenAI)")
    st.caption("Paste references or upload a file. Each entry is validated against OpenAlex (ground truth); we report Found / Not found, journal in AJG master, and any mismatches (e.g. BibTeX vs OpenAlex).")
    refs_file = st.file_uploader("Upload .txt or .bib (optional)", type=["txt", "bib"], help="TXT: one reference per line. BIB: BibTeX entries; DOIs and titles are used for lookup.")
    refs_text = st.text_area(
        "Or paste references here (one per line). Ignored if a file is uploaded.",
        height=100,
        placeholder="e.g.\nSmith, J. (2023). Title. Journal of Finance. https://doi.org/10.1234/xyz\nOr one DOI per line: 10.1234/xyz",
    )
    if st.button("Validate against OpenAlex"):
        refs_raw: list[str | dict] = []
        if refs_file is not None:
            try:
                raw = refs_file.read().decode("utf-8", errors="replace")
            except Exception:
                raw = ""
            if refs_file.name.lower().endswith(".bib"):
                parsed = parse_bibtex_string(raw)
                refs_raw = parsed if parsed else [ln.strip() for ln in raw.strip().splitlines() if ln.strip()]
            else:
                refs_raw = [ln.strip() for ln in raw.strip().splitlines() if ln.strip()]
        else:
            pasted = (refs_text or "").strip()
            # If pasted text looks like BibTeX (e.g. @article{...), parse as BibTeX so we get one row per entry, not per line
            if pasted and re.search(r"@\w+\s*\{", pasted, re.IGNORECASE):
                parsed = parse_bibtex_string(pasted)
                refs_raw = parsed if parsed else [ln.strip() for ln in pasted.splitlines() if ln.strip()]
            else:
                refs_raw = [ln.strip() for ln in pasted.splitlines() if ln.strip()]
        if not refs_raw:
            st.warning("Paste at least one reference line or upload a .txt / .bib file.")
        else:
            master_df = load_master()
            total_refs = len(refs_raw)
            results = []

            progress_bar = st.progress(0.0, text="Starting validation…")
            status_placeholder = st.empty()
            counts_placeholder = st.empty()

            for i, ref in enumerate(refs_raw):
                is_bib = isinstance(ref, dict)
                if is_bib:
                    doi = (ref.get("doi") or "").strip() or None
                    title = (ref.get("title") or "").strip()
                    journal_bib = (ref.get("journal") or "").strip()
                    year_bib = (ref.get("year") or "").strip()
                    snippet = (ref.get("snippet") or title or journal_bib or "")[:80]
                else:
                    line = str(ref)
                    doi = extract_doi(line)
                    title = journal_bib = year_bib = ""
                    snippet = line[:80] + ("…" if len(line) > 80 else "")

                pct = (i + 1) / total_refs
                progress_bar.progress(min(pct, 1.0), text=f"Reference {i + 1} of {total_refs} ({100 * pct:.0f}%)")
                status_placeholder.caption(f"**Checking:** {snippet or '(no title)'}")
                found_so_far = sum(1 for r in results if r["Status"] == "Found")
                not_found_so_far = len(results) - found_so_far
                counts_placeholder.caption(f"✓ Found: **{found_so_far}** · ✗ Not found: **{not_found_so_far}**")

                work = openalex_work_by_doi(doi) if doi else None
                if work is None and (title or snippet):
                    search_snippet = (title or (snippet if is_bib else re.sub(DOI_PATTERN, "", str(ref)).strip()))[:120]
                    search_snippet = " ".join(search_snippet.split())  # normalize whitespace
                    if len(search_snippet) >= 4:
                        works = openalex_work_by_search(search_snippet, per_page=1)
                        work = works[0] if works else None
                if work is None:
                    results.append({
                        "Reference (snippet)": snippet,
                        "Status": "Not found",
                        "OpenAlex title": "",
                        "Year": "",
                        "Journal (OpenAlex)": "",
                        "In AJG master?": "",
                        "AJG 2024": "",
                        "Warnings": "No match in OpenAlex",
                        "Link": "",
                    })
                    continue
                oa_title = work.get("display_name") or ""
                oa_year = (work.get("publication_date") or "")[:4] or ""
                jname, jissn = get_journal_from_work(work)
                master_row = find_journal_in_master(master_df, jname, jissn) if master_df is not None else None
                in_ajg = "Yes" if master_row is not None else "No"
                ajg24 = (master_row["AJG 2024"] if master_row is not None and "AJG 2024" in master_row else "") or ""
                warnings = []
                if not doi and work:
                    warnings.append("Matched by search; verify it is the right work.")
                if master_row is None and jname:
                    warnings.append("Journal not in AJG 2024 master.")
                if is_bib and year_bib and oa_year and year_bib != oa_year:
                    warnings.append(f"Year mismatch: BibTeX={year_bib}, OpenAlex={oa_year}")
                if is_bib and journal_bib and jname and normalize_title_for_match(journal_bib) != normalize_title_for_match(jname):
                    warnings.append("Journal name differs from OpenAlex.")
                link = work.get("id") or (f"https://doi.org/{(work.get('ids') or {}).get('doi', '')}" or "")
                results.append({
                    "Reference (snippet)": snippet,
                    "Status": "Found",
                    "OpenAlex title": oa_title[:70] + ("…" if len(oa_title) > 70 else ""),
                    "_oa_title_full": oa_title,  # for corrected .bib export
                    "Year": oa_year,
                    "Journal (OpenAlex)": (jname or "")[:50] + ("…" if len(jname or "") > 50 else ""),
                    "_oa_journal_full": jname or "",  # for corrected .bib export
                    "In AJG master?": in_ajg,
                    "AJG 2024": str(ajg24),
                    "Warnings": "; ".join(warnings) if warnings else "—",
                    "Link": link,
                })

            progress_bar.progress(1.0, text=f"Done — validated {total_refs} reference(s)")
            status_placeholder.empty()
            counts_placeholder.empty()

            st.dataframe(
                pd.DataFrame(results),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Link": st.column_config.LinkColumn("Link", display_text="Open"),
                },
            )
            found = sum(1 for r in results if r["Status"] == "Found")
            st.caption(f"**{found}** of {len(results)} references found in OpenAlex. Use OpenAlex as ground truth; treat “Not found” or “Journal not in AJG master” as prompts to verify.")

            has_bib = any(isinstance(r, dict) and r.get("raw_block") for r in refs_raw)
            if has_bib and found > 0:
                corrected_bib = build_corrected_bibtex(results, refs_raw)
                if corrected_bib:
                    st.download_button(
                        "Download corrected .bib (Found only, year/journal/title from OpenAlex)",
                        data=corrected_bib,
                        mime="application/x-bibtex",
                        file_name="references_corrected.bib",
                        key="dl_corrected_bib",
                    )
                    st.caption("Contains only references that were found. Year, journal, and title are updated from OpenAlex where they differed.")


    st.divider()
    st.caption("Data: AJG 2024 master + JCR • Literature: [OpenAlex](https://openalex.org) (no API key required)")

    st.sidebar.divider()
    st.sidebar.caption("Data: ajg_2024_master_with_jcr.csv • Literature: OpenAlex")


if __name__ == "__main__":
    main()
