# Red team: digitization validation (ajg_2024_ground_truth.csv)

## Summary

The digitization output had **systematic parsing bugs**. **Parser fix applied** (stop reading value lines when the next line is a field code). After re-run:

- **Column bleed:** 0 (was 171).
- **British Accounting Review:** Present.
- **Row count:** 1,786 (was 1,312).
- **Remaining:** False “Evaluation” rows (2) and any other split-title cases; optional post-pass or LlamaParse for those.

---

## Issues that were fixed

1. **Column bleed** — The 12th column sometimes contained the next row’s field code (e.g. `ACCOUNT`) instead of the numeric value. **Fix:** Parser stops reading value lines when it sees a field line and does not consume it.
2. **Missing journals** — e.g. British Accounting Review was dropped. **Fix:** Same; we no longer consume the next row’s field.

## Remaining edge cases

- **False “Evaluation” row** — A title fragment from “International Journal of Accounting, Auditing and Performance **Evaluation**” can appear as a standalone journal when the PDF layout splits the title. Optional: merge or drop in post-processing, or re-digitize with LlamaParse.
- **Merged / malformed rows** — Rows with very few values in the PDF could previously pull in the next row’s field and title; the fix reduces but may not eliminate all such cases.

## Data quality checks (post-fix)

- No field code in last column.
- British Accounting Review present in ACCOUNT with correct metrics.
- Spot-check a sample of rows against the PDF.

**Fix applied** in `digitize_ajg2024_from_pdf.py`; section 6 checks in the original report are satisfied (bleed=0, British Accounting Review present).
