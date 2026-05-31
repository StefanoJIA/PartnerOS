# Public-Source Enrichment MVP

**Status:** current on 2026-05-30.

## Purpose

Public-source enrichment supports Lead Intelligence by gathering limited, reviewable website evidence for a company and turning it into pending suggestions.

It is evidence-first and human-in-the-loop. It must not replace operator judgment, silently overwrite CRM facts, or become a general crawler.

## Current Flow

```text
Company website -> Enrichment run -> Source evidence -> Suggestions -> Review -> Apply accepted items
```

The company must have a website. The enrichment runner may inspect limited same-origin paths such as:

- `/`
- `/about`
- `/products`
- `/services`
- `/solutions`
- `/contact`

The implementation must keep host restrictions, SSRF protections, timeouts, response-size limits, text-length limits, and page-count limits. `PUBLIC_ENRICHMENT_ENABLED=false` disables outbound enrichment runs.

## Suggestion Types

| Type | Meaning |
|---|---|
| `business_summary` | Draft company summary from public evidence |
| `tag` | Suggested formal tag |
| `market_segment` | Suggested Lead Intelligence segment slug |
| `score_hint` | Candidate scoring context, not the formal score |

Suggestions default to pending. Accepted suggestions may be applied through explicit operator action. Rejected suggestions stay recorded so weak evidence is not reintroduced without context.

## Apply Behavior

| Type | Apply behavior |
|---|---|
| `tag` | Create or reuse `Tag`, then attach it through `ObjectTag(company)` |
| `business_summary` | Update `Company.business_description` |
| `market_segment` | Merge the segment slug into company product-interest context |
| `score_hint` | Store as an explanatory note, not as the formal lead score |

Apply actions must write an activity log and must not trigger outreach or external notifications.

## Evidence Rules

Every suggestion should preserve:

- source URL
- captured title or excerpt
- matched phrase or reason
- capture time
- review status

Evidence can be stale, marketing-heavy, incomplete, or ambiguous. It is a suggestion layer, not the formal customer profile.

## Safety Boundaries

Public-source enrichment must not:

- run broad crawling, search-engine harvesting, or off-origin browsing
- scrape LinkedIn or other restricted platforms
- send email, campaigns, webhooks, or automatic outreach
- create RFQs, quotes, orders, shipments, or feedback tickets
- notify customers or suppliers
- call carrier APIs
- expose tokens, raw response bodies, backend storage paths, local files, internal costs, margins, supplier private notes, or secrets
- privilege any manufacturing partner by hard-coded name

## Validation

```powershell
cd backend
python scripts/lead_intelligence_docs_check.py
python scripts/project_execution_chain_check.py
```

## Related Docs

- [Lead Intelligence MVP](lead_intelligence_mvp.md)
- [Lead Intelligence Scoring Notes](lead_intelligence_scoring_notes.md)
- [Product Vision](product_vision.md)
