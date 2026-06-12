# D8.26 Staging Seed Selection Checklist

Status: READY_FOR_STAGING_HANDOFF  
External staging state: WAITING_FOR_REAL_STAGING_EVIDENCE  
Selection status: pending

No real business owner sign-off recorded yet. This checklist helps the business owner choose staging-safe seed records for partner rehearsal, staging UAT, and pilot. Pending records must not be written as approved.

## Classification Rules

Every candidate record must carry both source and visibility classification.

Source classification:

- demo seed
- sanitized real record
- synthetic sample
- pending

Visibility classification:

- customer-safe
- internal-only
- requires approval

Rules:

- Do not write pending records as approved.
- Do not use sanitized real record as customer-visible until business owner sign-off is complete.
- Do not present synthetic sample as real customer data, real partner feedback, or real staging evidence.
- Do not expose forbidden fields through any seed record.

## Products Checklist

| Record | Partner | Product Family | Source | Visibility | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| HOSUN product seed | HOSUN | lifting systems / desk frames / desk legs / lifting columns / heavy-duty supply | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | Technical claims require review |
| JOOBOO product seed | JOOBOO | education furniture / school desks/chairs / project furniture | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | Project furniture wording requires review |
| future partner product seed | future partner | onboarding data / product family | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | Partner-specific fields required |

## Customers Checklist

| Record | Segment | Source | Visibility | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| HOSUN customer segment | distributor / project buyer | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | No real customer identity without approval |
| JOOBOO customer segment | school / institution / project buyer | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | Procurement context must be sanitized |
| future partner segment | pending | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | Segment wording required |

## Quotes Checklist

| Record | Partner | Source | Visibility | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| HOSUN quote sample | HOSUN | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | No cost, margin, pricing breakdown |
| JOOBOO quote sample | JOOBOO | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | No private procurement assumptions |
| future partner quote sample | future partner | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | Quote logic remains internal-only |

## Orders Checklist

| Record | Partner | Source | Visibility | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| HOSUN order sample | HOSUN | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | No PO, PI, contract, supplier note, unsafe raw ID |
| JOOBOO order sample | JOOBOO | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | No real school identity or private delivery notes |
| future partner order sample | future partner | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | Delivery requirement wording requires review |

## Production Milestones Checklist

| Record | Partner | Source | Visibility | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| HOSUN production milestone | HOSUN | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | Planned dates must say planned / 预计 |
| JOOBOO production milestone | JOOBOO | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | Project acceptance criteria require review |
| future partner production milestone | future partner | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | Partner-specific milestone wording required |

## Shipment Status Checklist

| Record | Partner | Source | Visibility | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| HOSUN shipment status | HOSUN | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | Shipment risk must be customer-safe wording |
| JOOBOO shipment status | JOOBOO | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | Delivery consistency wording requires review |
| future partner shipment status | future partner | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | Delivery requirement remains internal until approved |

## Resources Checklist

| Record | Partner | Source | Visibility | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| HOSUN resource | HOSUN | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | No backend paths or storage keys |
| JOOBOO resource | JOOBOO | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | Resource needs require business wording |
| future partner resource | future partner | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | Resource taxonomy must be reviewed |

## Feedback Checklist

| Record | Partner | Source | Visibility | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| HOSUN feedback | HOSUN | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | No complaint details or warranty cost exposure |
| JOOBOO feedback | JOOBOO | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | Feedback after use must be sanitized |
| future partner feedback | future partner | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | Customer-visible feedback fields required |

## Market Response Preview Checklist

| Record | Partner | Source | Visibility | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| HOSUN Market Response preview | HOSUN | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | No internal scoring or ranking |
| JOOBOO Market Response preview | JOOBOO | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | No private project prioritization |
| future partner Market Response preview | future partner | demo seed / sanitized real record / synthetic sample / pending | customer-safe / internal-only / requires approval | pending | Market Response metrics require review |

## Boundary

- Pending records must not be written as approved.
- No real staging seed has been approved.
- Do not enter D9.
- Do not create proof records.
- Do not write STAGING_VALIDATED.
- Do not fabricate real sign-off.
- Do not fabricate real partner feedback.
