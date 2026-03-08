# OpenAlex search & filter reference (for Works)

Use this to enrich the literature search in the Journal Lookup app. All of these can be combined with filtering by journal ISSN.

---

## 1. Full-text search (`search`)

Find works by words in **title, abstract, or fulltext**.

| Parameter | Example | Notes |
|-----------|---------|--------|
| `search` | `search=corporate governance` | Stemming + stop words; words ANDed |
| `search.exact` | `search.exact=surgery` | No stemming, exact word |
| `search.semantic` | `search.semantic=machine learning in healthcare` | **Meaning-based** (beta); 1 req/sec, max 50 results |

**Boolean and phrases:**

- `search=(elmo AND "sesame street") NOT (cookie OR monster)`
- Phrase: `search="climate change"`
- Proximity: `search="climate change"~5` (within 5 words)
- Wildcards: `search=machin*` (machine, machines, …); `search=wom?n`
- Fuzzy (typos): `search=machin~1`

**Note:** Search requests cost more than filter-only ($1 vs $0.10 per 1k calls). One `search` (or `.exact` or `.semantic`) per request.

---

## 2. Filters (combine with commas = AND)

### Date

| Filter | Example |
|--------|---------|
| `from_publication_date` | `from_publication_date:2020-01-01` |
| `to_publication_date` | `to_publication_date:2023-12-31` |
| `publication_year` | `publication_year:2022` |

### Open access

| Filter | Example |
|--------|---------|
| `is_oa` | `is_oa:true` (only OA works) |
| `oa_status` | `oa_status:gold`, `green`, `hybrid`, `bronze`, `closed` |

### Type of work

| Filter | Example |
|--------|---------|
| `type` | `type:article`, `book`, `dataset`, `dissertation`, etc. |

### Impact / content

| Filter | Example |
|--------|---------|
| `cited_by_count` | `cited_by_count:>10` (min citations) |
| `has_abstract` | `has_abstract:true` |
| `has_doi` | `has_doi:true` |
| `has_pdf_url` | `has_pdf_url:true` |

### Author & institution

| Filter | Example |
|--------|---------|
| `author.id` | OpenAlex author ID |
| `authorships.institutions.country_code` | `authorships.institutions.country_code:gb` |
| `institutions.id` | OpenAlex institution ID |

### Topic / concept

| Filter | Example |
|--------|---------|
| `concepts.id` | OpenAlex concept ID |
| `primary_topic.id` | OpenAlex topic ID |
| `sustainable_development_goals.id` | SDG ID |

### Other

| Filter | Example |
|--------|---------|
| `language` | `language:en` (ISO 639-1) |
| `is_retracted` | `is_retracted:false` (exclude retractions) |

**Inequality:** `cited_by_count:>100`, `publication_year:>2019`  
**Negation:** `country_code:!us`  
**OR (same attribute):** `country_code:gb|fr`

---

## 3. Sort (`sort`)

| Sort | Example | Use |
|------|---------|-----|
| `publication_date` | `sort=publication_date:desc` | Newest first |
| `cited_by_count` | `sort=cited_by_count:desc` | Most cited first |
| `relevance_score` | `sort=relevance_score:desc` | Only when using `search` |

Default for search is relevance; for filter-only, add `sort=publication_date:desc` for recency.

---

## 4. Example combined request

Works in a journal (by ISSN), from 2020, open access only, with “board” in title/abstract, sorted by citations:

```
GET https://api.openalex.org/works?
  filter=primary_location.source.issn:0304-405X,from_publication_date:2020-01-01,is_oa:true
  &search=board
  &sort=cited_by_count:desc
  &per-page=25
```

---

## 5. Useful app enrichments

- **Text search:** Optional `search` box (title/abstract/fulltext).
- **Open access only:** Checkbox → `is_oa:true`.
- **Sort:** Dropdown: “Newest first” (publication_date:desc) vs “Most cited” (cited_by_count:desc).
- **End year:** `to_publication_date` in addition to “from year”.
- **Work type:** Restrict to `type:article` (or allow article/book/dataset).
- **Min citations:** Optional `cited_by_count:>N`.
- **Semantic search (beta):** Optional “Search by meaning” using `search.semantic` (rate-limited, max 50).
