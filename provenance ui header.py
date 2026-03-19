"""
Reference mockup — design now integrated into journal_lookup_app.py.

- Hero + fonts + section_header() live in main() and the UI helpers in that file.
- Keep this file as a standalone preview snippet if you want to experiment without touching the app.
"""

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Provenance — Journal Lookup & Literature",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global styles ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;1,400&family=DM+Mono:wght@400;500&display=swap');

    /* Scope all overrides to avoid stomping Streamlit chrome */
    .prov-root { font-family: 'EB Garamond', Georgia, serif; }

    .prov-eyebrow {
        font-family: 'DM Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #888;
        margin-bottom: 0.5rem;
    }
    .prov-title {
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 2.6rem;
        font-weight: 400;
        letter-spacing: -0.01em;
        line-height: 1.15;
        margin-bottom: 0.2rem;
    }
    .prov-ipa {
        font-family: 'DM Mono', monospace;
        font-size: 0.8rem;
        color: #aaa;
        margin-bottom: 1.2rem;
    }
    .prov-rule {
        border: none;
        border-top: 1px solid #e0e0e0;
        margin-bottom: 1.2rem;
    }
    .prov-def {
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 1.15rem;
        font-style: italic;
        color: #555;
        line-height: 1.6;
        margin-bottom: 1rem;
    }
    .prov-statement {
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 1rem;
        line-height: 1.8;
        margin-bottom: 1rem;
    }
    .prov-coda {
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 0.95rem;
        color: #555;
        line-height: 1.8;
        border-left: 2px solid #ccc;
        padding-left: 1rem;
        margin-bottom: 0;
    }

    /* Section headers */
    .prov-section-label {
        font-family: 'DM Mono', monospace;
        font-size: 0.68rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #aaa;
        margin-bottom: 0.2rem;
    }
    .prov-section-title {
        font-family: 'EB Garamond', Georgia, serif;
        font-size: 1.5rem;
        font-weight: 400;
        margin-bottom: 0.25rem;
    }
    .prov-section-caption {
        font-size: 0.88rem;
        color: #666;
        line-height: 1.6;
        margin-bottom: 0;
    }

    /* Reduce Streamlit top padding */
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Hero header ───────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="prov-root">
      <p class="prov-eyebrow">quinference.com / provenance</p>
      <h1 class="prov-title">Provenance</h1>
      <p class="prov-ipa">/ˈprɒv.ə.nəns/</p>
      <hr class="prov-rule">
      <p class="prov-def">The origin and custodial history of a source.</p>
      <p class="prov-statement">
        In archival scholarship, provenance determines whether a record can be trusted.
        In the age of generative AI, the same question applies to every citation:
        not merely <em>does this paper exist</em>, but <em>does it exist where and as claimed?</em>
      </p>
      <p class="prov-coda">
        This tool applies that standard systematically — tracing each reference back to its
        source in OpenAlex and the AJG 2024 master, so that the scholarly record remains
        what it has always been required to be: verifiable.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── Helper: section header ────────────────────────────────────────────────────
def section_header(roman: str, label: str, title: str, caption: str) -> None:
    """Render a typographically consistent section header."""
    st.markdown(
        f"""
        <div class="prov-root" style="padding: 1.25rem 0 0.5rem; border: none;">
          <p class="prov-section-label">{roman}. {label}</p>
          <h2 class="prov-section-title">{title}</h2>
          <p class="prov-section-caption">{caption}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ── Usage: replace the three st.header / st.subheader calls as follows ────────
#
# REPLACE:
#   st.header("Journals")
# WITH:
#   section_header(
#       "I", "Journal index",
#       "Browse AJG 2024",
#       "Filter by field, grade, and JCR quartile. Search by journal name.",
#   )
#
# REPLACE:
#   st.subheader("Literature search (OpenAlex)")
#   st.caption("Fetch articles for selected journals ...")
# WITH:
#   section_header(
#       "II", "Literature",
#       "Search via OpenAlex",
#       "Retrieve recent works from selected journals. "
#       "Filter by year, open access, keyword, and citation count.",
#   )
#
# REPLACE:
#   st.subheader("Sanity check references (GenAI)")
#   st.caption("Paste references or upload a file ...")
# WITH:
#   section_header(
#       "III", "Validation",
#       "Sanity-check references",
#       "Paste or upload references — including BibTeX from GenAI tools — "
#       "and verify each against OpenAlex ground truth.",
#   )