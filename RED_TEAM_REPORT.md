# Red team: ajg_2024_ground_truth.csv

## Summary

The digitization output had **systematic parsing bugs**. **Parser fix applied** (stop reading value lines when the next line is a field code). After re-run:

- **Column bleed:** 0 (was 171).
- **British Accounting Review:** Present.
- **Row count:** 1,786 (was 1,312).
- **Remaining:** False “Evaluation” rows (2) and any other split-title cases; optional post-pass or LlamaParse for those.

Original findings below; fix is in place.

---

## 1. Column bleed (critical)

**What:** The 12th column (“Citations policy docs (2017-21)”) often contains the **next row’s field code** (e.g. `ACCOUNT`, `ECON`, `BUS HIST & ECON HIST`) instead of a number.

**Cause:** The parser always reads exactly 10 lines for the numeric columns. When a row has fewer than 10 values in the PDF (e.g. missing JIF or other rank), the “10th” line is already the next row’s field code. That line is written into the last column and the next row’s first line (the real journal title) is then treated as the start of a new row.

**Observed:** **171 rows** have a field code in the last column.

**Impact:** Wrong values in “Citations policy docs”; downstream analytics (e.g. means, filters) are wrong. Some journals are effectively **dropped** because the next line (the real title) is consumed as the start of a new row and can get mis-parsed.

**Example (row 14):**  
`...,0.030,ACCOUNT` → last column should be `0.030`; `ACCOUNT` is the next row’s field.

---

## 2. Missing journals (critical)

**What:** At least one journal present in the PDF is **missing** from the CSV.

**Example:** **British Accounting Review** (ACCOUNT, 3, 3, 6, 10, 14, 5, 45%, 44%, 4%, 0.301) does not appear. It is the row immediately after “Behavioral Research in Accounting”. Because the parser reads the next line (“ACCOUNT”) as the 10th value for that row, the line “British Accounting Review” is then treated as the title of a new row; the following 10 lines are attached to it, but the **next** line is again “ACCOUNT” (for British Tax Review), so British Tax Review’s title gets merged or the row count is wrong. So the loss of British Accounting Review is a direct consequence of the 10-line read.

**Impact:** Any use of the CSV as a complete list (e.g. “all 3+ in ACCOUNT”) is wrong; REF/reporting would undercount.

---

## 3. False “journal” row (medium)

**What:** A **title fragment** is emitted as a standalone journal.

**Example:** Row with title **“Evaluation”** (and grades 2, 2, 68, 73, 74, …). In the PDF this is the continuation of **“International Journal of Accounting, Auditing and Performance Evaluation”**; the layout split the title across two lines, and PyMuPDF put “Evaluation” on its own line. The parser then treats it as a new journal.

**Impact:** One spurious journal; duplicate/inflated counts if you do “all journals in ACCOUNT” and also wrong assignment of the metrics (they belong to the full title).

---

## 4. Merged / malformed rows (medium)

**What:** Some CSV rows contain **two journals** or broken titles.

**Examples:**

- **Row 21:** `Journal of Financial Reporting,3,ACCOUNT,"Journal of International Accounting, Auditing and Taxation",3,3,...` — two journals in one row; “Journal of Financial Reporting” has only grade 3 in the PDF (no other metrics), and the next row’s field + title are concatenated.
- **Rows 47–49:** Multiple journals in one row (e.g. “International Journal of Critical Accounting” + “Journal of Accounting and Management Information Systems” + “Journal of Accounting and Taxation”); and a broken title **“of Forensic Accounting)”** (should be “Journal of Forensic and Investigative Accounting (previously Journal of Forensic Accounting)”).

**Cause:** When a row in the PDF has very few values (e.g. only grade), the parser still reads 10 lines, so it pulls in the next row’s field and title. That produces merged rows and broken titles.

**Impact:** Wrong journal–metrics mapping; duplicate or missing journals in lookups.

---

## 5. Row count vs source (low)

**What:** CSV has **1,312 data rows**; the existing `ajg_journal_rankings_2024.csv` has **1,424**. The PDF is the authority, so the target is “all rows in the PDF”, not 1,424. After fixing the parser, the count may go up (recover missing journals) and some bad rows may be removed or split, so the final count should be re-checked against the PDF.

---

## 6. Data quality checks to run after a fix

- **No field code in last column:** `Citations policy docs` must never equal a known field code (ACCOUNT, ECON, etc.).
- **British Accounting Review present** in ACCOUNT with grades 3, 3 and the correct metrics.
- **No standalone title “Evaluation”** (merge with “International Journal of Accounting, Auditing and Performance Evaluation” or drop as duplicate).
- **No row** where the “Journal Title” field contains a field code (e.g. ACCOUNT) or where two distinct journal names appear in one row.
- **Spot-check:** Compare a sample of rows (by field and title) to the PDF to confirm alignment.

---

## Recommended fix (parser)

- After reading the **first grade** for a row, **do not** always read exactly 10 lines. Instead:
  - Read the next line: if it is a **field line** (e.g. `_is_field_line(ln)`), **do not** consume it and **stop** reading; pad the row’s remaining columns with empty strings so you have 10 values.
  - Otherwise append it to the row’s numeric values and repeat until you have 10 values or you hit a field line.
- That way you never consume the next row’s field, so no column bleed and no missing journals like British Accounting Review.
- Optionally: detect and merge continuation title fragments (e.g. “Evaluation” after “International Journal of Accounting, Auditing and Performance”) or document them for manual review.

**Fix applied:** Parser now stops reading value lines when it sees a field line (does not consume it). Re-run completed; section 6 checks: bleed=0, British Accounting Review present. “Evaluation” and merged-row edge cases remain for optional cleanup.
