# OpenAlex search & filter reference (Works API)

Use this to enrich the literature search in the Journal Lookup app. All options can be combined with filtering by journal ISSN.

---

## 1. Full-text search (`search`)

Find works by words in **title, abstract, or fulltext**.

| Parameter | Example | Notes |
|-----------|---------|--------|
| `search` | `search=corporate governance` | Stemming + stop words; words ANDed |
| `search.exact` | `search.exact=surgery` | No stemming, exact word |
| `search.semantic` | `search.semantic=machine learning in healthcare` | **Meaning-based** (beta); 1 req/sec, max 50 results |

**Boolean and phrases:** `AND`, `OR`, `NOT`; phrase `"climate change"`; proximity `"climate change"~5`; wildcards `machin*`, `wom?n`; fuzzy `machin~1`.

**Note:** Search requests cost more than filter-only. One `search` (or `.exact` or `.semantic`) per request.

---

## 2. Filters (combine with commas = AND)

**Date:** `from_publication_date`, `to_publication_date`, `publication_year`  
**Open access:** `is_oa:true`, `oa_status:gold|green|hybrid|bronze|closed`  
**Type:** `type:article`, `book`, `dataset`, etc.  
**Impact:** `cited_by_count:>10`  
**Content:** `has_abstract:true`, `has_doi:true`, `has_pdf_url:true`  
**Author/place:** `author.id`, `authorships.institutions.country_code:gb`  
**Topic:** `concepts.id`, `primary_topic.id`, `sustainable_development_goals.id`  
**Other:** `language:en`, `is_retracted:false`  

Inequality: `cited_by_count:>100`. Negation: `country_code:!us`. OR: `country_code:gb|fr`.

---

## 3. Sort (`sort`)

`publication_date:desc` (newest first), `cited_by_count:desc` (most cited), `relevance_score:desc` (when using search).

---

## 4. Example

Works in a journal (ISSN), from 2020, open access, with “board” in title/abstract, sorted by citations:

```
filter=primary_location.source.issn:0304-405X,from_publication_date:2020-01-01,is_oa:true
&search=board
&sort=cited_by_count:desc
&per-page=25
```

See [OpenAlex API docs](https://docs.openalex.org/) for full reference.
