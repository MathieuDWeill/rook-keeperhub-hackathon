import json
from uuid import UUID

from apps.api.app.keeperhub import KeeperHubExecutor
from apps.api.app.models import (
    DecisionStatus,
    Evidence,
    EvidenceKind,
    PolicyDecision,
    ReleaseRequest,
)


def request() -> ReleaseRequest:
    return ReleaseRequest(
        project_id=UUID("00000000-0000-0000-0000-000000000001"),
        milestone_id="milestone-1",
        amount_minor=3_000_000,
        recipient="0x" + "1" * 40,
        escrow_contract="0x" + "2" * 40,
        client_accepted=True,
        invoice_verified=True,
        compliance_clear=True,
        evidence=[
            Evidence(
                kind=EvidenceKind.SIGNED_ACCEPTANCE,
                uri="ipfs://acceptance",
                sha256="a" * 64,
                verified=True,
            )
        ],
    )


def test_contract_call_payload_matches_keeperhub_api(monkeypatch):
    monkeypatch.setenv("CHAIN_ID", "11155111")
    executor = KeeperHubExecutor()
    decision = PolicyDecision(
        decision_id=UUID("00000000-0000-0000-0000-000000000099"),
        status=DecisionStatus.APPROVED,
        reasons=["ok"],
        releasable_amount_minor=2_850_000,
        retained_amount_minor=150_000,
    )
    payload = executor._contract_call_payload(request(), decision)
    assert payload["functionName"] == "release"
    assert payload["chainId"] == 11155111
    args = json.loads(payload["functionArgs"])
    assert len(args) == 4
    assert args[2] == request().recipient
    assert args[3] == "2850000"
    assert json.loads(payload["abi"])[0]["name"] == "release"
