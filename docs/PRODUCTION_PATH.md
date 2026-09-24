# From reference transaction to production

| Gate | Deliverable | Required proof |
| --- | --- | --- |
| 0 — OSS reference | Strict spec, proposal eligibility, paired-case math, offline verifier | CI passes, malformed inputs and tampering rejected, synthetic claims visible |
| 1 — Verified benchmark adapter | OutcomeBench manifest, protocol and scorecard verification | Original inputs replayed with OutcomeBench `verify`; evidence class and limitations preserved |
| 2 — A2Z handoff | Idempotent, consented job creation and status sync | Job ID reconciliation, duplicate/retry tests, no credentials in public artifacts |
| 3 — Private pilot | One consenting customer, authorized reviewer, scoped export | Data-processing agreement, baseline lock, redaction and retention review, signed decision |
| 4 — Managed service | Partner qualification, milestones, dispute and rework process | Measured delivery cost, first-pass acceptance, time to value, support load and collections |
| 5 — Multi-customer product | Tenant isolation, RBAC, audit, billing and support | Security review, incident exercises, recovery testing, financial reconciliation and independent customer references |

No gate is met by README breadth or synthetic passing scores. The first externally meaningful proof is a customer-authorized pilot where the buyer can reject the result, rerun the calculation, and compare delivery cost with an agreed baseline. Prospective commercial matching must distinguish verified provider qualifications from self-declared proposal text.

## Evaluation parameters

Measure work-spec completion time, fraction of proposals eligible, proposal-to-selection time, implementation lead time, first-pass acceptance, rework rate, recorded cost per accepted resolution, verifier failure rate, evidence completeness, disputes, support hours, buyer retention and collected contribution margin. Segment by support workload, buyer size, provider, region, evidence class and protocol version. Report sample sizes and missing data. Never mix synthetic, customer-supplied unverified, and independently verified observations in one leaderboard.
