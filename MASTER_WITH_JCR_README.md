# Patched master: ajg_2024_master_with_jcr.csv

This file is the **AJG 2024 ground truth** (from `ajg_2024_ground_truth.csv`) with **extra journal metrics** patched in from:

- **JCR_ABS.csv** – 2021 JIF, JCI, Eigenfactor, Article Influence Score, quartiles, Total Citations, Publisher, ISSN, JCR Category
- **BarryQuinn_JCR_JournalResults_11_2024.csv** (and -2, -3, -4, -5) – 2023 JIF, JCI, quartiles, Eigenfactor, AIS, Total Citations, JCR Category

## How it was built

Run:

```bash
python patch_master_with_jcr_metrics.py
```

Optional: `--master ajg_2024_ground_truth.csv --out ajg_2024_master_with_jcr.csv --dir .`

Matching is by **normalized journal title** (and Field for JCR_ABS). When a journal appears in more than one BarryQuinn file (e.g. Business and Management), the **first match** is used.

## Column list

| Column | Source | Description |
|--------|--------|-------------|
| Field … Citations policy docs (2017-21) | Master (PDF) | Original ground-truth columns |
| ISSN | JCR_ABS | ISSN (no hyphens in current output) |
| Publisher | JCR_ABS | Publisher name |
| JCR_2021_JIF | JCR_ABS | 2021 Journal Impact Factor |
| JCR_2021_JCI | JCR_ABS | 2021 JCR Citation Index |
| JCR_2021_JIF_Quartile | JCR_ABS | Q1–Q4 |
| JCR_2021_Total_Citations | JCR_ABS | Total citations |
| Eigenfactor | JCR_ABS | Eigenfactor score |
| Article_Influence_Score | JCR_ABS | Article Influence Score |
| JCR_Category | JCR_ABS | JCR category (e.g. BUSINESS, FINANCE - SSCI) |
| JCR_2023_JIF | BarryQuinn | 2023 JIF |
| JCR_2023_JCI | BarryQuinn | 2023 JCI |
| JCR_2023_JIF_Quartile | BarryQuinn | Q1–Q4 |
| JCR_2023_Total_Citations | BarryQuinn | Total citations |
| JCR_2023_Eigenfactor | BarryQuinn | Eigenfactor |
| JCR_2023_AIS | BarryQuinn | Article Influence Score |
| JCR_2023_Category | BarryQuinn | JCR category |

Empty cells mean no match in that source.

## Match counts (typical run)

- Master rows: 1,786  
- Matched JCR_ABS: ~1,256  
- Matched BarryQuinn (2023 JCR): ~872  

Unmatched rows are still in the file; JCR columns are blank for them.
