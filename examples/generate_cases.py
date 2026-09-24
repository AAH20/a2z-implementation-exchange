"""Regenerate the committed 40-paired-case synthetic fixture exactly."""

import json
from pathlib import Path

cases = []
for arm in ("baseline", "candidate"):
    for index in range(1, 41):
        cases.append({
            "arm": arm,
            "case_id": f"CASE-{index:03d}",
            "accepted": index <= (32 if arm == "baseline" else 36),
            "cost_usd": 28 if arm == "baseline" else 22,
        })
path = Path(__file__).with_name("cases.json")
path.write_text(json.dumps(cases, indent=2) + "\n", encoding="utf-8")
print(path)
