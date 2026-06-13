# D8.33 Response Intake Rules

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE  
Intake status: rules only, no real response recorded

No real external response is recorded here. These rules define how to record replies after a human manually sends D8.32 messages and pastes the real response into the repository workflow.

## Core Intake Rules

- Only when the user pastes a real reply may the tracker status become `response received`.
- Do not write internal guesses as external replies.
- Do not write presenter assumptions as partner feedback.
- Do not write oral, unconfirmed content as sign-off.
- Raw token must not enter docs; if a counterparty provides a token, record only `PROVIDED_VIA_SECURE_CHANNEL`.
- Business sign-off must include explicit owner, date, and scope.
- Security approval must include explicit reviewer, date, and scope.
- Partner feedback must be classified as original quote, internal observation, system issue, or roadmap candidate.
- Pending must not be written as approved or complete.

## Response Type Classification

| Source | Allowed Classification | Required Evidence | Status Rule |
| --- | --- | --- | --- |
| partner stakeholder | original quote | pasted exact words or approved transcript | may become response received |
| presenter | internal observation | presenter note, not partner quote | may become response received only as internal observation |
| operator | system issue | reproducible issue or clear operating note | may become response received as system issue |
| product/business team | roadmap candidate | requested capability or planning candidate | may become response received as roadmap candidate |
| business owner | business sign-off | owner, date, scope, approved fields/conditions | can update sign-off doc, not tracker status alone |
| security reviewer | security approval | reviewer, date, scope, reviewed areas, required fixes | can update sign-off doc, not tracker status alone |
| credential owner | credentials status | redacted status only | token value must be `PROVIDED_VIA_SECURE_CHANNEL` |

## Token Handling Rule

If a real token is sent by any party:

1. Do not paste it into Git, docs, logs, screenshots, or chat.
2. Move the actual token through the approved secure channel.
3. Record only `PROVIDED_VIA_SECURE_CHANNEL`.
4. If token exposure occurred, mark security review blocked and require revocation/rotation.

## Sign-Off Rule

Business sign-off is valid only if it includes:

- owner
- date
- scope
- approved fields or changes required
- conditions

Security approval is valid only if it includes:

- reviewer
- date
- scope
- reviewed areas
- required fixes or approval status

Without these fields, record the reply as `response received` or `changes requested`, not approved.

## HOSUN Intake Rule

HOSUN replies about lifting systems, desk frames, desk legs, lifting columns, heavy-duty supply, load, stability, noise, delivery, installation, after-sales, packaging, warranty, test cycle, certification, or project demand must be classified as:

- customer-safe candidate
- needs validation
- internal-only
- pilot blocker

Do not expose raw test notes, complaint details, delivery risk analysis, warranty cost exposure, supplier private notes, or internal Market Response scoring as customer-visible content.

## JOOBOO And Future Partner Intake Rule

JOOBOO replies must track education furniture, school desks/chairs, project furniture, school procurement timing, delivery consistency, installation, resource needs, feedback after use, and project acceptance criteria.

Future partner replies must track onboarding data, product family, quote logic, delivery requirement, resource taxonomy, customer-visible fields, and Market Response metrics.

## Boundary

- No real response recorded here.
- Do not fabricate credentials, evidence, sign-off, or partner feedback.
- Do not mark pending as approved or complete.
- Do not write STAGING_VALIDATED.
- Do not enter D9.
- Do not create proof records.
