"""Inspectable, offline implementation transaction for a support AI pilot.

The reference runtime handles invented data only. It never runs a support agent,
contacts a worker, provisions infrastructure, or transfers money.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

VERSION = "0.1.0"
WORKLOAD = "AI-assisted customer support"


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def _object(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{label} must contain exactly {sorted(keys)}")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonempty text")
    return value.strip()


def _number(value: Any, label: str, minimum: float = 0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < minimum:
        raise ValueError(f"{label} must be finite and at least {minimum}")
    return float(value)


def validate_spec(spec: Any) -> dict[str, Any]:
    spec = _object(spec, {"id", "title", "workload", "objective", "currency", "budget_usd", "minimum_cases_per_arm", "minimum_acceptance_rate", "maximum_cost_per_accepted_usd", "required_capabilities", "evidence_class"}, "spec")
    for key in ("id", "title", "objective"):
        _text(spec[key], f"spec.{key}")
    if spec["workload"] != WORKLOAD or spec["currency"] != "USD" or spec["evidence_class"] != "SYNTHETIC":
        raise ValueError("reference runtime supports synthetic USD support work only")
    _number(spec["budget_usd"], "budget_usd")
    minimum = spec["minimum_cases_per_arm"]
    if isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 30:
        raise ValueError("minimum_cases_per_arm must be an integer >= 30")
    rate = _number(spec["minimum_acceptance_rate"], "minimum_acceptance_rate")
    if rate > 1:
        raise ValueError("minimum_acceptance_rate cannot exceed 1")
    _number(spec["maximum_cost_per_accepted_usd"], "maximum_cost_per_accepted_usd")
    capabilities = spec["required_capabilities"]
    if not isinstance(capabilities, list) or not capabilities or any(not isinstance(x, str) or not x.strip() for x in capabilities) or len(capabilities) != len(set(capabilities)):
        raise ValueError("required_capabilities must be unique nonempty strings")
    return spec


def validate_proposals(spec: dict[str, Any], proposals: Any) -> list[dict[str, Any]]:
    if not isinstance(proposals, list) or not proposals:
        raise ValueError("at least one proposal is required")
    ids: set[str] = set()
    for p in proposals:
        _object(p, {"id", "provider_label", "worker_type", "capabilities", "bid_usd", "delivery_days", "plan", "disclosures"}, "proposal")
        pid = _text(p["id"], "proposal.id")
        _text(p["provider_label"], "provider_label")
        _text(p["plan"], "plan")
        if pid in ids:
            raise ValueError("duplicate proposal id")
        ids.add(pid)
        if p["worker_type"] not in ("human", "agent", "swarm"):
            raise ValueError("unsupported worker type")
        if not isinstance(p["capabilities"], list) or any(not isinstance(c, str) for c in p["capabilities"]):
            raise ValueError("invalid capabilities")
        _number(p["bid_usd"], "bid_usd")
        if isinstance(p["delivery_days"], bool) or not isinstance(p["delivery_days"], int) or p["delivery_days"] < 1:
            raise ValueError("delivery_days must be positive")
        if not isinstance(p["disclosures"], list) or any(not isinstance(d, str) for d in p["disclosures"]):
            raise ValueError("disclosures must be text list")
    return proposals


def compare_proposals(spec: dict[str, Any], proposals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    required = set(spec["required_capabilities"])
    comparison = []
    for p in proposals:
        missing = sorted(required - set(p["capabilities"]))
        reasons = []
        if missing:
            reasons.append("MISSING_CAPABILITY")
        if p["bid_usd"] > spec["budget_usd"]:
            reasons.append("OVER_BUDGET")
        comparison.append({"proposal_id": p["id"], "eligible": not reasons, "reasons": reasons, "missing_capabilities": missing, "bid_usd": p["bid_usd"], "delivery_days": p["delivery_days"]})
    return sorted(comparison, key=lambda x: (not x["eligible"], x["bid_usd"], x["delivery_days"], x["proposal_id"]))


def validate_selection(selection: Any, proposals: list[dict[str, Any]], comparison: list[dict[str, Any]]) -> None:
    _object(selection, {"proposal_id", "buyer_reviewer", "rationale"}, "selection")
    _text(selection["buyer_reviewer"], "buyer_reviewer")
    _text(selection["rationale"], "selection.rationale")
    if selection["proposal_id"] not in {p["id"] for p in proposals}:
        raise ValueError("unknown selected proposal")
    if not next(c for c in comparison if c["proposal_id"] == selection["proposal_id"])["eligible"]:
        raise ValueError("selected proposal is ineligible")


def evaluate(spec: dict[str, Any], cases: Any) -> dict[str, Any]:
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases must be a nonempty list")
    arms: dict[str, dict[str, Any]] = {}
    for arm in ("baseline", "candidate"):
        rows = [r for r in cases if isinstance(r, dict) and r.get("arm") == arm]
        seen: set[str] = set()
        total = 0.0
        accepted = 0
        for row in rows:
            _object(row, {"arm", "case_id", "accepted", "cost_usd"}, "case")
            case_id = _text(row["case_id"], "case_id")
            if case_id in seen:
                raise ValueError("duplicate case id in arm")
            seen.add(case_id)
            if type(row["accepted"]) is not bool:
                raise ValueError("accepted must be boolean")
            accepted += int(row["accepted"])
            total += _number(row["cost_usd"], "case cost")
        arms[arm] = {"eligible_cases": len(rows), "accepted_cases": accepted, "acceptance_rate": round(accepted / len(rows), 6) if rows else 0, "total_cost_usd": round(total, 2), "cost_per_accepted_usd": round(total / accepted, 2) if accepted else None}
    if len(cases) != sum(a["eligible_cases"] for a in arms.values()):
        raise ValueError("unknown case arm or malformed case")
    baseline_ids = {r["case_id"] for r in cases if r["arm"] == "baseline"}
    candidate_ids = {r["case_id"] for r in cases if r["arm"] == "candidate"}
    gates = {
        "minimum_sample_met": all(a["eligible_cases"] >= spec["minimum_cases_per_arm"] for a in arms.values()),
        "case_mix_identical": baseline_ids == candidate_ids,
        "candidate_quality_floor_met": arms["candidate"]["acceptance_rate"] >= spec["minimum_acceptance_rate"],
        "candidate_cost_ceiling_met": arms["candidate"]["cost_per_accepted_usd"] is not None and arms["candidate"]["cost_per_accepted_usd"] <= spec["maximum_cost_per_accepted_usd"],
    }
    return {"metrics": arms, "gates": gates, "all_gates_met": all(gates.values()), "claim_scope": "SYNTHETIC_RECORDED_CASE_ARITHMETIC_ONLY"}


def a2z_job(spec: dict[str, Any]) -> dict[str, Any]:
    """Payload compatible with A2Z Agent Hire's create_job input contract."""
    return {"id": spec["id"], "title": spec["title"], "objective": spec["objective"], "budget_usd": spec["budget_usd"], "customer_price_usd": spec["budget_usd"], "acceptance_criteria": [
        {"id": "SAMPLE", "description": f"At least {spec['minimum_cases_per_arm']} recorded cases per arm", "required": True},
        {"id": "QUALITY", "description": f"Candidate acceptance rate at least {spec['minimum_acceptance_rate']}", "required": True},
        {"id": "COST", "description": f"Candidate cost per accepted resolution at most USD {spec['maximum_cost_per_accepted_usd']}", "required": True},
        {"id": "BUYER_ACCEPTANCE", "description": "Named buyer reviewer explicitly accepts", "required": True},
    ], "worker_policy": {"allowed_worker_types": ["human", "agent", "swarm"], "requires_independent_verifier": True}, "economics": {key: 0 for key in ("worker_payout_usd", "model_cost_usd", "compute_cost_usd", "human_review_cost_usd", "payment_fee_usd", "support_reserve_usd", "rework_reserve_usd")}, "evidence_class": "SYNTHETIC"}


def build(spec: Any, proposals: Any, selection: Any, cases: Any, decision: Any) -> dict[str, Any]:
    spec = validate_spec(spec)
    proposals = validate_proposals(spec, proposals)
    comparison = compare_proposals(spec, proposals)
    validate_selection(selection, proposals, comparison)
    evaluation = evaluate(spec, cases)
    _object(decision, {"status", "buyer_reviewer", "rationale"}, "decision")
    if decision["status"] not in ("ACCEPTED", "REJECTED"):
        raise ValueError("decision.status must be ACCEPTED or REJECTED")
    _text(decision["buyer_reviewer"], "decision.buyer_reviewer")
    _text(decision["rationale"], "decision.rationale")
    if decision["status"] == "ACCEPTED" and not evaluation["all_gates_met"]:
        raise ValueError("cannot accept when evaluation gates fail")
    chosen = next(p for p in proposals if p["id"] == selection["proposal_id"])
    gross = round(spec["budget_usd"] - chosen["bid_usd"], 2)
    body = {"schema_version": VERSION, "evidence_class": "SYNTHETIC", "spec": spec, "spec_sha256": digest(spec), "a2z_agent_hire_job": a2z_job(spec), "proposals": proposals, "comparison": comparison, "selection": selection, "cases": cases, "evaluation": evaluation, "decision": decision, "economics": {"illustrative_buyer_budget_usd": spec["budget_usd"], "selected_bid_usd": chosen["bid_usd"], "unallocated_budget_usd": gross, "realized_revenue_usd": 0, "realized_profit_usd": 0, "note": "Budget minus bid is not margin; fees, support, tax, rework, collection and acquisition costs are excluded."}, "limits": ["Synthetic cases and provider labels; no customer or worker was contacted.", "Recorded arithmetic does not establish causal lift or production suitability.", "A human buyer decision is recorded as supplied text, not authenticated.", "No payment, provisioning or external API call occurs."]}
    return {**body, "package_sha256": digest(body)}


def verify(package: Any) -> bool:
    if not isinstance(package, dict) or "package_sha256" not in package:
        raise ValueError("invalid package")
    expected = build(package.get("spec"), package.get("proposals"), package.get("selection"), package.get("cases"), package.get("decision"))
    if canonical(expected) != canonical(package):
        raise ValueError("package differs from recomputed inputs")
    return True
