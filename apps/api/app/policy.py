from __future__ import annotations

import hashlib
import json
from uuid import UUID

from .models import DecisionStatus, EvidenceKind, PolicyDecision, ReleaseRequest

POLICY_VERSION = "rook-policy/1.0.0"


def _decision_uuid(request: ReleaseRequest) -> UUID:
    """Stable decision id for the same immutable mandate.

    The id deliberately excludes requested_at so retries generate the same KeeperHub
    idempotency key and the escrow rejects a duplicate release onchain.
    """
    canonical = {
        "project_id": str(request.project_id),
        "milestone_id": request.milestone_id,
        "amount_minor": request.amount_minor,
        "token": request.token,
        "recipient": request.recipient.lower(),
        "escrow_contract": request.escrow_contract.lower(),
        "evidence": sorted(
            [
                {
                    "kind": item.kind.value,
                    "sha256": item.sha256.lower(),
                    "verified": item.verified,
                }
                for item in request.evidence
            ],
            key=lambda item: (item["kind"], item["sha256"]),
        ),
        "client_accepted": request.client_accepted,
        "invoice_verified": request.invoice_verified,
        "compliance_clear": request.compliance_clear,
        "dispute_open": request.dispute_open,
        "retention_bps": request.retention_bps,
        "policy_version": POLICY_VERSION,
    }
    digest = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).digest()
    return UUID(bytes=digest[:16], version=5)


def evaluate_release(request: ReleaseRequest) -> PolicyDecision:
    reasons: list[str] = []
    verified_kinds = {item.kind for item in request.evidence if item.verified}

    if request.dispute_open:
        reasons.append("An open dispute blocks automated release")
    if not request.client_accepted:
        reasons.append("Client acceptance is missing")
    if not request.invoice_verified:
        reasons.append("Invoice verification is missing")
    if not request.compliance_clear:
        reasons.append("Compliance checks are not clear")
    if EvidenceKind.SIGNED_ACCEPTANCE not in verified_kinds:
        reasons.append("No verified signed acceptance evidence")
    if EvidenceKind.INVOICE not in verified_kinds:
        reasons.append("No verified invoice evidence")

    decision_id = _decision_uuid(request)
    if reasons:
        return PolicyDecision(
            decision_id=decision_id,
            status=DecisionStatus.REJECTED,
            reasons=reasons,
            policy_version=POLICY_VERSION,
        )

    retained = request.amount_minor * request.retention_bps // 10_000
    releasable = request.amount_minor - retained
    return PolicyDecision(
        decision_id=decision_id,
        status=DecisionStatus.APPROVED,
        reasons=["All mandatory controls passed"],
        releasable_amount_minor=releasable,
        retained_amount_minor=retained,
        policy_version=POLICY_VERSION,
    )
