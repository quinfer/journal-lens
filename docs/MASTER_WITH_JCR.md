# Patched master: ajg_2024_master_with_jcr.csv

The app’s data source. It is the **AJG 2024 ground truth** (from `ajg_2024_ground_truth.csv`) with **JCR metrics** merged in from:

- **JCR_ABS.csv** — 2021 JIF, JCI, Eigenfactor, AIS, quartiles, Total Citations, Publisher, ISSN, JCR Category  
- **BarryQuinn_JCR_JournalResults_11_2024*.csv** — 2023 JIF, JCI, quartiles, Eigenfactor, AIS, Total Citations, JCR Category  

## Build

```bash
python patch_master_with_jcr_metrics.py
```

Optional: `--master ajg_2024_ground_truth.csv --out ajg_2024_master_with_jcr.csv --dir .`

Matching is by **normalized journal title** (and Field for JCR_ABS). First match wins when a journal appears in multiple JCR category files.

## Columns (summary)

| Source | Columns added |
|--------|----------------|
| Master (PDF) | Field, Journal Title, AJG 2024/2021, Citescore/SNIP/SJR/JIF ranks, SDG %, co-authorship %, etc. |
| JCR_ABS | ISSN, Publisher, JCR_2021_JIF, JCR_2021_JCI, JCR_2021_JIF_Quartile, JCR_2021_Total_Citations, Eigenfactor, Article_Influence_Score, JCR_Category |
| BarryQuinn | JCR_2023_JIF, JCR_2023_JCI, JCR_2023_JIF_Quartile, JCR_2023_Total_Citations, JCR_2023_Eigenfactor, JCR_2023_AIS, JCR_2023_Category |

Empty cells mean no match in that source. Typical run: ~1,786 master rows; ~1,256 matched to JCR_ABS; ~872 to BarryQuinn 2023.
