from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
checks = []


def add(name, ok, detail):
    checks.append({"check": name, "ok": bool(ok), "detail": detail})


def run(cmd):
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    return p.returncode == 0, (p.stdout + p.stderr).strip()[-1200:]


def is_generated(path):
    return bool({".git", ".venv", "__pycache__", "node_modules"} & set(path.parts))


def json_file(path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


required = [
    "README.md",
    "LICENSE",
    "SECURITY.md",
    "CODEX_FINALIZE_HACKATHON.md",
    "contracts/package-lock.json",
    "artifacts/openapi.json",
    "docs/VIDEO_SCRIPT.md",
    "docs/SUBMISSION_CHECKLIST.md",
]
for f in required:
    path = ROOT / f
    add(f"file:{f}", path.is_file(), "present" if path.is_file() else "missing")

for pat in ("**/__pycache__", "**/*.pyc", "**/.DS_Store"):
    hits = [path for path in ROOT.glob(pat) if not is_generated(path.relative_to(ROOT))]
    add(
        f"clean:{pat}",
        not hits,
        ", ".join(str(x.relative_to(ROOT)) for x in hits[:5]) or "clean",
    )

ok, out = run([sys.executable, "-m", "pytest", "-q"])
add("python-tests", ok, out)
ok, out = run([sys.executable, "scripts/demo_smoke.py"])
add("demo-smoke", ok, out)
lock = ROOT / "contracts/package-lock.json"
add("npm-lockfile", lock.exists(), "reproducible npm install via npm ci")
if (ROOT/"contracts/node_modules/.bin/hardhat").exists():
    ok, out = run(["bash", "-lc", "cd contracts && npm test"])
    add("solidity-tests", ok, out)
else:
    add(
        "solidity-tests",
        False,
        "not run locally; execute `cd contracts && npm ci && npm test`",
    )

required_live = [
    "KEEPERHUB_API_KEY",
    "RPC_URL",
    "DEPLOYER_PRIVATE_KEY",
    "ARTISAN_ADDRESS",
]
missing = [k for k in required_live if not os.getenv(k)]
add("live-secrets", not missing, "configured" if not missing else "missing: " + ", ".join(missing))

deployment = json_file(ROOT / "artifacts/deployment.json")
deployment_ok = bool(deployment.get("escrow") and deployment.get("mockUsdc"))
add(
    "live-deployment",
    deployment_ok,
    "deployment.json has escrow and mockUsdc" if deployment_ok else "missing deployed escrow/mockUsdc",
)

proof = json_file(ROOT / "artifacts/live-proof.json")
execution = proof.get("execution") or {}
proof_ok = bool(execution.get("execution_id") and execution.get("tx_hash") and execution.get("explorer_url"))
add(
    "live-transaction-proof",
    proof_ok,
    "execution id, transaction hash and explorer link saved" if proof_ok else "missing live KeeperHub transaction proof",
)
summary = {
    "ready_for_local_demo": all(
        c["ok"] for c in checks if c["check"] not in {"solidity-tests", "live-secrets"}
    ),
    "ready_for_live_submission": all(c["ok"] for c in checks),
    "checks": checks,
}
(ROOT / "artifacts/submission-manifest.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
sys.exit(0 if summary["ready_for_local_demo"] else 1)
