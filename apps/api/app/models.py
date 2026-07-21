from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


class EvidenceKind(StrEnum):
    SIGNED_ACCEPTANCE = "signed_acceptance"
    INVOICE = "invoice"
    PHOTO = "photo"
    COMPLIANCE_DOCUMENT = "compliance_document"


class Evidence(BaseModel):
    kind: EvidenceKind
    uri: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    verified: bool = False


class ReleaseRequest(BaseModel):
    project_id: UUID = Field(default_factory=uuid4)
    milestone_id: str = Field(min_length=1, max_length=80)
    amount_minor: int = Field(gt=0, description="Token amount in smallest unit")
    token: str = Field(default="USDC", pattern=r"^[A-Z0-9]{2,12}$")
    recipient: str = Field(pattern=r"^0x[a-fA-F0-9]{40}$")
    escrow_contract: str = Field(pattern=r"^0x[a-fA-F0-9]{40}$")
    evidence: list[Evidence] = Field(default_factory=list)
    client_accepted: bool = False
    invoice_verified: bool = False
    compliance_clear: bool = False
    dispute_open: bool = False
    retention_bps: int = Field(default=500, ge=0, le=2_000)
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def require_evidence(self) -> "ReleaseRequest":
        if not self.evidence:
            raise ValueError("At least one evidence item is required")
        return self


class DecisionStatus(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"


class PolicyDecision(BaseModel):
    decision_id: UUID = Field(default_factory=uuid4)
    status: DecisionStatus
    reasons: list[str]
    releasable_amount_minor: int = 0
    retained_amount_minor: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    policy_version: str = "rook-policy/1.0.0"


class ExecutionResult(BaseModel):
    mode: str
    status: str
    execution_id: str | None = None
    tx_hash: str | None = None
    explorer_url: str | None = None
    simulation: dict[str, Any] = Field(default_factory=dict)
    raw: dict[str, Any] = Field(default_factory=dict)


class ReleaseResponse(BaseModel):
    request: ReleaseRequest
    decision: PolicyDecision
    execution: ExecutionResult | None = None
