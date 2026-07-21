from __future__ import annotations
import json
import os
from pathlib import Path

root = Path(__file__).resolve().parents[1]
deployment_path = root / "artifacts/deployment.json"
deployment = json.loads(deployment_path.read_text()) if deployment_path.exists() else {}
values = {
    "REPOSITORY_URL": os.getenv("REPOSITORY_URL", "<ADD_GITHUB_URL>"),
    "DEMO_VIDEO_URL": os.getenv("DEMO_VIDEO_URL", "<ADD_VIDEO_URL>"),
    "TRANSACTION_URL": os.getenv("TRANSACTION_URL", "<ADD_KEEPERHUB_TRANSACTION_URL>"),
    "CONTRACT_ADDRESS": deployment.get("escrow", "<ADD_ESCROW_ADDRESS>"),
}
template = (root / "docs/SUBMISSION_TEMPLATE.md").read_text()
for key, value in values.items():
    template = template.replace("{{" + key + "}}", value)
out = root / "artifacts/DORAHACKS_SUBMISSION.md"
out.write_text(template)
print(out)
