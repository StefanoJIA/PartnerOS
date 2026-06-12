# D8.26 HOSUN Lifting Systems Field Review

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE  
Review status: pending

No real business owner sign-off recorded yet. This field review prepares HOSUN lifting systems data for future partner rehearsal, staging UAT, and pilot. It does not approve any customer-visible HOSUN claim.

## Product Scope

HOSUN field review must cover:

- lifting systems
- desk frames
- desk legs
- lifting columns
- heavy-duty supply

## HOSUN Field Review Matrix

Each field must be classified as customer-safe candidate, internal-only, needs validation, needs business wording, or pilot blocker.

| Field | Customer-Safe Candidate | Internal-Only | Needs Validation | Needs Business Wording | Pilot Blocker |
| --- | --- | --- | --- | --- | --- |
| load | load range after approval | raw load test notes and exception cases | yes | yes | yes if unsupported |
| stability | stability summary after approval | raw stability test notes and supplier comments | yes | yes | yes if unsupported |
| noise | noise claim after approval | raw noise test data and complaint details | yes | yes | yes if unsupported |
| delivery | planned delivery window | delivery risk analysis and supplier escalation | yes | yes | yes if customer-visible timing is unclear |
| installation | installation summary | unresolved installation risk and internal troubleshooting | yes | yes | yes if instructions are not approved |
| after-sales | after-sales support summary | complaint details and internal service cost | yes | yes | yes if support commitment is unclear |
| packaging | packaging summary | packaging failure notes and supplier corrective actions | yes | yes | yes if packaging claim is unsupported |
| warranty | warranty summary after approval | warranty cost exposure and private claim analysis | yes | yes | yes if terms are unsupported |
| test cycle | test cycle summary after approval | raw test cycle logs and lab notes | yes | yes | yes if source material is missing |
| certification | certification summary after approval | draft certification notes and unresolved gaps | yes | yes | yes if certification cannot be supported |
| project demand | project demand category | internal demand scoring and private account notes | yes | yes | yes if segment wording is unsafe |

## Customer-Visible Rule For Sensitive Metrics

load, noise, test cycle, certification, and warranty can only become customer-visible after both conditions are met:

1. Business owner confirms the exact customer-safe wording.
2. Supporting product material exists and is approved for external use.

Until both conditions are met, these fields remain pending and must not be written as approved.

## Internal-Only HOSUN Fields

The following must remain internal-only:

- raw test notes
- complaint details
- delivery risk analysis
- warranty cost exposure
- supplier private notes
- internal Market Response scoring
- private partner notes
- backend paths
- storage keys
- token values
- unsafe raw database IDs

## Customer-Safe Candidate HOSUN Fields

The following may be prepared as customer-safe candidates, subject to business wording and supporting material:

- product family
- load range
- stability summary
- noise claim
- delivery window
- installation summary
- after-sales support
- warranty summary
- test cycle summary
- certification summary
- packaging summary
- project demand category

## JOOBOO Coverage

JOOBOO remains a peer partner path. Field preparation should cover:

- education furniture
- school desks/chairs
- project furniture
- school procurement timing
- delivery consistency
- installation
- resource needs
- feedback after use
- project acceptance criteria

JOOBOO project wording must not expose real school identity, private procurement notes, or private project acceptance issues before business owner sign-off.

## Future Partner Coverage

Future partner field preparation must cover:

- onboarding data
- product family
- quote logic
- delivery requirement
- resource taxonomy
- customer-visible fields
- Market Response metrics

Partner-specific quote logic, delivery requirements, and Market Response metrics remain internal-only until reviewed and signed off.

## Boundary

- No real HOSUN field approval has been recorded.
- No real business owner sign-off recorded yet.
- Pending fields must not be written as approved.
- Do not write STAGING_VALIDATED.
- Do not enter D9.
- Do not create proof records.
- Do not fabricate real sign-off or real partner feedback.
