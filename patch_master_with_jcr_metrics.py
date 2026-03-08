#!/usr/bin/env python3
"""
Patch the AJG 2024 ground-truth master CSV with extra journal metrics from:
  - JCR_ABS.csv (2021 JIF, JCI, Eigenfactor, AIS, quartiles, etc.)
  - BarryQuinn_JCR_JournalResults_11_2024*.csv (2023 JIF, JCI, quartiles, etc.)
  - Optionally 3and4and4stars.csv / Updated_Missing_... for Eigenfactor when missing

Match by normalized journal title (and Field for JCR_ABS). Uses first match when
a journal appears in multiple JCR category files.

Usage:
  python patch_master_with_jcr_metrics.py
  python patch_master_with_jcr_metrics.py --master ajg_2024_ground_truth.csv --out master_with_jcr.csv
"""

import argparse
import csv
import re
from pathlib import Path


def normalize_title(s: str) -> str:
    if not s or not isinstance(s, str):
        return ""
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = s.replace("&", " and ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def load_master(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        return list(r)


def load_csv(path: str) -> tuple[list[str], list[dict]]:
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        fieldnames = r.fieldnames or []
        rows = list(r)
    return fieldnames, rows


def build_jcr_abs_lookup(rows: list[dict]) -> dict[tuple[str, str], dict]:
    """Key (field, norm_title) -> {ISSN, 2021 JIF, Eigenfactor, ...}."""
    out = {}
    for row in rows:
        field = (row.get("Field") or "").strip()
        title = (row.get("Journal Title") or "").strip()
        if not title:
            continue
        key = (field, normalize_title(title))
        if key in out:
            continue
        out[key] = {
            "ISSN": (row.get("ISSN") or row.get("ISSN.y") or "").strip().replace("-", ""),
            "Publisher": (row.get("Publisher Name") or "").strip(),
            "JCR_2021_JIF": (row.get("2021 JIF") or "").strip(),
            "JCR_2021_JCI": (row.get("2021 JCI") or "").strip(),
            "JCR_2021_JIF_Quartile": (row.get("JIF Quartile") or "").strip(),
            "JCR_2021_Total_Citations": (row.get("Total Citations") or "").strip().replace(",", ""),
            "Eigenfactor": (row.get("Eigenfactor") or "").strip(),
            "Article_Influence_Score": (row.get("Article Influence Score") or "").strip(),
            "JCR_Category": (row.get("Category") or "").strip(),
        }
    return out


def build_barry_quinn_lookup(rows: list[dict]) -> dict[str, dict]:
    """Key norm_title or ISSN -> {2023 JIF, 2023 JCI, ...}. First match wins."""
    out = {}
    for row in rows:
        name = (row.get("Journal name") or "").strip()
        issn = (row.get("ISSN") or "").strip().replace("-", "")
        if not name and not issn:
            continue
        key = normalize_title(name)
        if key and key not in out:
            out[key] = {
                "JCR_2023_JIF": (row.get("2023 JIF") or "").strip(),
                "JCR_2023_JCI": (row.get("2023 JCI") or "").strip(),
                "JCR_2023_JIF_Quartile": (row.get("JIF Quartile") or "").strip(),
                "JCR_2023_Total_Citations": (row.get("Total Citations") or "").strip().replace(",", ""),
                "JCR_2023_Eigenfactor": (row.get("Eigenfactor") or "").strip(),
                "JCR_2023_AIS": (row.get("Article Influence Score") or "").strip(),
                "JCR_2023_Category": (row.get("Category") or "").strip(),
            }
        if issn and issn not in out:
            out[issn] = out.get(key, {})
    return out


def merge_barry_quinn_lookups(lookups: list[dict]) -> dict:
    """Merge multiple BarryQuinn lookups; first match per key wins."""
    merged = {}
    for lu in lookups:
        for k, v in lu.items():
            merged.setdefault(k, v)
    return merged


def main() -> None:
    ap = argparse.ArgumentParser(description="Patch master CSV with JCR and other metrics.")
    ap.add_argument("--master", default="ajg_2024_ground_truth.csv", help="Master ground-truth CSV")
    ap.add_argument("--out", default="ajg_2024_master_with_jcr.csv", help="Output patched CSV")
    ap.add_argument("--dir", default=".", help="Directory containing CSVs")
    args = ap.parse_args()
    base = Path(args.dir)
    master_path = base / args.master
    out_path = base / args.out

    if not master_path.exists():
        raise SystemExit(f"Master not found: {master_path}")

    master = load_master(str(master_path))
    if not master:
        raise SystemExit("Master has no rows.")

    fieldnames_in = list(master[0].keys())

    # JCR_ABS
    jcr_abs_path = base / "JCR_ABS.csv"
    jcr_abs_lu = {}
    if jcr_abs_path.exists():
        _, jcr_abs_rows = load_csv(str(jcr_abs_path))
        jcr_abs_lu = build_jcr_abs_lookup(jcr_abs_rows)

    # BarryQuinn JCR 2023 (all -2, -3, -4, -5 and base)
    barry_files = [
        base / "BarryQuinn_JCR_JournalResults_11_2024.csv",
        base / "BarryQuinn_JCR_JournalResults_11_2024-2.csv",
        base / "BarryQuinn_JCR_JournalResults_11_2024-3.csv",
        base / "BarryQuinn_JCR_JournalResults_11_2024-4.csv",
        base / "BarryQuinn_JCR_JournalResults_11_2024-5.csv",
    ]
    barry_lookups = []
    for p in barry_files:
        if p.exists():
            _, rows = load_csv(str(p))
            barry_lookups.append(build_barry_quinn_lookup(rows))
    barry_lu = merge_barry_quinn_lookups(barry_lookups) if barry_lookups else {}

    # Extra columns we will add (order)
    extra_cols = [
        "ISSN",
        "Publisher",
        "JCR_2021_JIF",
        "JCR_2021_JCI",
        "JCR_2021_JIF_Quartile",
        "JCR_2021_Total_Citations",
        "Eigenfactor",
        "Article_Influence_Score",
        "JCR_Category",
        "JCR_2023_JIF",
        "JCR_2023_JCI",
        "JCR_2023_JIF_Quartile",
        "JCR_2023_Total_Citations",
        "JCR_2023_Eigenfactor",
        "JCR_2023_AIS",
        "JCR_2023_Category",
    ]
    out_fieldnames = fieldnames_in + extra_cols

    matched_abs = 0
    matched_barry = 0
    out_rows = []
    for row in master:
        field = (row.get("Field") or "").strip()
        title = (row.get("Journal Title") or "").strip()
        norm = normalize_title(title)
        new_row = dict(row)

        # JCR_ABS: match on (Field, norm_title)
        abs_key = (field, norm)
        abs_data = jcr_abs_lu.get(abs_key) or jcr_abs_lu.get(("", norm))
        if abs_data:
            matched_abs += 1
            for c in extra_cols:
                if c in abs_data and c not in new_row:
                    new_row[c] = abs_data.get(c, "")
        else:
            for c in extra_cols:
                if c not in new_row:
                    new_row[c] = ""

        # BarryQuinn 2023: match on norm_title or ISSN from JCR_ABS
        barry_data = barry_lu.get(norm)
        if not barry_data and abs_data and abs_data.get("ISSN"):
            barry_data = barry_lu.get(abs_data["ISSN"])
        if barry_data:
            matched_barry += 1
            for k, v in barry_data.items():
                if v and (not new_row.get(k) or k.startswith("JCR_2023")):
                    new_row[k] = v

        out_rows.append(new_row)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(out_rows)

    print(f"Master rows: {len(master)}")
    print(f"Matched JCR_ABS: {matched_abs}")
    print(f"Matched BarryQuinn (2023 JCR): {matched_barry}")
    print(f"Written: {out_path}")


if __name__ == "__main__":
    main()
