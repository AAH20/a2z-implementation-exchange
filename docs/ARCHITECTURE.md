# Architecture and commercial boundary

## OSS reference system

```mermaid
flowchart TB
  subgraph Intake[1. Buyer intake]
    Spec[Versioned work spec]
    Budget[Budget and acceptance thresholds]
    Consent[Evidence class and scope]
  end
  subgraph Supply[2. Proposal comparison]
    Proposals[Provider and worker proposals]
    Eligibility[Capabilities plus budget eligibility]
    BuyerChoice[Named human selection and rationale]
  end
  subgraph Delivery[3. Recorded delivery evidence]
    Baseline[Baseline case records]
    Candidate[Candidate case records]
    Pairing[Identical case ID check]
    Metrics[Accepted count, rate, total cost, cost per accepted]
  end
  subgraph Close[4. Decision and verification]
    Gates[Sample, quality, cost, case mix gates]
    Acceptance[Named buyer acceptance or rejection]
    Package[Canonical JSON and SHA-256]
    Replay[Independent local recomputation]
  end
  Spec --> Eligibility
  Budget --> Eligibility
  Consent --> Package
  Proposals --> Eligibility --> BuyerChoice
  Baseline --> Pairing
  Candidate --> Pairing --> Metrics --> Gates
  BuyerChoice --> Package
  Gates --> Acceptance --> Package --> Replay
```

The core is pure Python and JSON. It makes no network requests. A transaction is built from five source inputs; derived fields are never trusted on verification. The verifier reconstructs the package and compares canonical JSON byte-for-byte. That detects accidental or deliberate changes inside the package, but cannot authenticate independently supplied source records.

## Data and authority model

```mermaid
erDiagram
  WORK_SPEC ||--o{ PROPOSAL : receives
  WORK_SPEC ||--|| BUYER_SELECTION : controls
  PROPOSAL ||--o| BUYER_SELECTION : selected_by
  WORK_SPEC ||--o{ CASE_RECORD : defines_evaluation
  CASE_RECORD }o--|| EVALUATION : contributes_to
  EVALUATION ||--|| BUYER_DECISION : informs
  BUYER_SELECTION ||--|| TRANSACTION_PACKAGE : recorded_in
  BUYER_DECISION ||--|| TRANSACTION_PACKAGE : recorded_in
  EVALUATION ||--|| TRANSACTION_PACKAGE : recorded_in
  WORK_SPEC {
    string id
    number budget_usd
    number minimum_acceptance_rate
    number maximum_cost_per_accepted_usd
  }
  PROPOSAL {
    string id
    string worker_type
    number bid_usd
    string[] capabilities
  }
  CASE_RECORD {
    string arm
    string case_id
    boolean accepted
    number cost_usd
  }
  EVALUATION {
    number eligible_cases
    number accepted_cases
    number cost_per_accepted_usd
    boolean all_gates_met
  }
  BUYER_DECISION {
    string status
    string buyer_reviewer
    string rationale
  }
```

The work spec fixes evaluation thresholds before the cases are scored. Provider eligibility is checked before selection. Evaluation gates constrain acceptance but do not make the buyer's decision. The named reviewer is text in v0.1, so the reference runtime does not establish legal authority or nonrepudiation.

## Existing ecosystem integration

```mermaid
flowchart LR
  Work[Implementation Exchange work spec] --> Export[A2Z compatible create_job JSON]
  Export --> Hire[A2Z Agent Hire OSS runtime]
  Delivery[Future consented support exports] --> Bridge[Outcome Fabric Evidence Bridge]
  Bridge --> Bench[OutcomeBench protocol and scorecard]
  Bench --> Adapter[Future verified scorecard adapter]
  Adapter --> Gate[Implementation acceptance gates]
  Work --> Gate
  Hire -. live API not implemented .-> Delivery
```

The current integration is a job payload matching A2Z Agent Hire's published `create_job` input fields. No live A2Z API call or OutcomeBench invocation is present. An OutcomeBench adapter should call OutcomeBench's own `verify(manifest, protocol, scorecard)` against original exports before mapping its metrics. Merely importing a JSON scorecard would be insufficient. The adapter must preserve its evidence class, comparison status, claim scope, and protocol hash, and refuse to convert descriptive results into a production recommendation.

## Prospective commercial product

```mermaid
flowchart TB
  BuyerOrg[Customer organization] --> IntakeService[Private intake and contract workflow]
  IntakeService --> ScopeDesk[Human scope and acceptance design]
  ScopeDesk --> Matching[Qualified partner matching]
  Matching --> Partner[Implementation partner]
  Partner --> DeliveryOps[Milestones, change control, support]
  DeliveryOps --> EvidenceOps[Consented private connectors and evidence review]
  EvidenceOps --> BuyerSignoff[Authorized buyer sign-off]
  BuyerSignoff --> Billing[Contractual invoicing and payout]
  OSS[OSS transaction and verifier] --> ScopeDesk
  OSS --> EvidenceOps
  OSS --> BuyerSignoff
  Security[Identity, tenant isolation, audit, retention] --> IntakeService
  Security --> EvidenceOps
  Security --> Billing
```

The commercial layer would sell implementation coordination, qualified delivery capacity, private connectors, review operations, support and contractual administration. The inspectable work spec, evaluation arithmetic, acceptance schema and offline verifier should remain OSS so buyers and partners can independently inspect the basic transaction. Private customer data, verified partner records and negotiated contract terms belong in tenant-controlled systems; they are not an algorithmic secret or a pretext to hide the acceptance math.

## Unit-economics contract

For each real implementation, track buyer contract value, signed provider payout, model and compute expense, human review, integration work, support reserve, rework, payment fees, acquisition expense, collections and refunds. `contribution_margin = collected_revenue - provider_payout - variable_delivery_costs - payment_fees - expected_rework`. Gross margin should be computed only after those inputs are measured. Separately, report customer outcome economics as `total_recorded_workload_cost / accepted_resolutions` for the locked measurement window. Do not add the one-time implementation fee to per-case cost unless explicitly amortized over a declared case volume and horizon.

The synthetic example has $5,000 budget and $3,200 bid. The $1,800 remainder is not margin because there is no sale and the rest of the cost stack is unspecified. The supported claim is reproducible arithmetic on invented cases.
