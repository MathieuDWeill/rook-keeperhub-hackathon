from uuid import UUID

from apps.api.app.models import Evidence, EvidenceKind, ReleaseRequest
from apps.api.app.policy import evaluate_release

ADDRESS = "0x" + "1" * 40
CONTRACT = "0x" + "2" * 40
HASH = "a" * 64
PROJECT = UUID("12345678-1234-5678-1234-567812345678")


def request(**overrides):
    data = dict(
        project_id=PROJECT,
        milestone_id="roof-complete",
        amount_minor=1_000_000,
        recipient=ADDRESS,
        escrow_contract=CONTRACT,
        evidence=[
            Evidence(kind=EvidenceKind.SIGNED_ACCEPTANCE, uri="ipfs://a", sha256=HASH, verified=True),
            Evidence(kind=EvidenceKind.INVOICE, uri="ipfs://b", sha256="b" * 64, verified=True),
        ],
        client_accepted=True,
        invoice_verified=True,
        compliance_clear=True,
        retention_bps=500,
    )
    data.update(overrides)
    return ReleaseRequest(**data)


def test_approved_release_and_retention():
    decision = evaluate_release(request())
    assert decision.status == "approved"
    assert decision.releasable_amount_minor == 950_000
    assert decision.retained_amount_minor == 50_000


def test_decision_id_is_stable_for_retries():
    assert evaluate_release(request()).decision_id == evaluate_release(request()).decision_id


def test_material_change_gets_new_decision_id():
    assert evaluate_release(request()).decision_id != evaluate_release(request(amount_minor=2_000_000)).decision_id


def test_missing_acceptance_is_rejected():
    decision = evaluate_release(request(client_accepted=False))
    assert decision.status == "rejected"
    assert "Client acceptance is missing" in decision.reasons


def test_dispute_blocks_execution():
    decision = evaluate_release(request(dispute_open=True))
    assert decision.status == "rejected"
