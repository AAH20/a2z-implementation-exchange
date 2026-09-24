import copy
import json
import unittest
from pathlib import Path

from implementation_exchange.core import build, compare_proposals, validate_spec, verify


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def inputs():
    return [json.loads((EXAMPLES / f"{name}.json").read_text()) for name in ("spec", "proposals", "selection", "cases", "decision")]


class TransactionTests(unittest.TestCase):
    def test_demo_acceptance_and_arithmetic(self):
        package = build(*inputs())
        self.assertTrue(verify(package))
        self.assertEqual(package["evaluation"]["metrics"]["baseline"]["cost_per_accepted_usd"], 35)
        self.assertEqual(package["evaluation"]["metrics"]["candidate"]["cost_per_accepted_usd"], 24.44)
        self.assertTrue(package["evaluation"]["all_gates_met"])
        self.assertEqual(package["economics"]["realized_profit_usd"], 0)
        self.assertEqual(package["a2z_agent_hire_job"]["id"], package["spec"]["id"])

    def test_tampered_metric_rejected(self):
        package = build(*inputs())
        package["evaluation"]["metrics"]["candidate"]["accepted_cases"] = 40
        with self.assertRaises(ValueError):
            verify(package)

    def test_failed_gate_cannot_be_accepted(self):
        values = inputs()
        for row in values[3]:
            if row["arm"] == "candidate":
                row["accepted"] = False
        with self.assertRaisesRegex(ValueError, "evaluation gates fail"):
            build(*values)

    def test_failed_gate_can_be_rejected(self):
        values = inputs()
        values[0]["maximum_cost_per_accepted_usd"] = 20
        values[4]["status"] = "REJECTED"
        package = build(*values)
        self.assertFalse(package["evaluation"]["all_gates_met"])
        self.assertTrue(verify(package))

    def test_ineligible_proposal_cannot_be_selected(self):
        values = inputs()
        values[2]["proposal_id"] = "PROPOSAL-B"
        with self.assertRaisesRegex(ValueError, "ineligible"):
            build(*values)

    def test_duplicate_case_rejected(self):
        values = inputs()
        values[3].append(copy.deepcopy(values[3][0]))
        with self.assertRaisesRegex(ValueError, "duplicate case"):
            build(*values)

    def test_case_mix_gate(self):
        values = inputs()
        values[3][-1]["case_id"] = "OTHER"
        values[4]["status"] = "REJECTED"
        self.assertFalse(build(*values)["evaluation"]["gates"]["case_mix_identical"])

    def test_strict_spec_and_proposal_sort(self):
        values = inputs()
        self.assertEqual(compare_proposals(validate_spec(values[0]), values[1])[0]["proposal_id"], "PROPOSAL-A")
        values[0]["unknown"] = True
        with self.assertRaises(ValueError):
            build(*values)

    def test_nonfinite_cost_rejected(self):
        values = inputs()
        values[3][0]["cost_usd"] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite"):
            build(*values)


if __name__ == "__main__":
    unittest.main()
