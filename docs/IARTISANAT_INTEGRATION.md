# Codex integration contract for iArtisanat

Do not copy the Streamlit hackathon UI into the product. Integrate the domain capability behind an interface.

## Product module

Suggested package/module name: `secure_payments` or `trust_payments`.

### Core entities

- `PaymentMandate`
- `ProjectEscrow`
- `Milestone`
- `EvidenceArtifact`
- `ReleaseDecision`
- `ExecutionAttempt`
- `Dispute`
- `Retention`

### Required application ports

```python
class ReleasePolicyPort(Protocol):
    def evaluate(self, mandate, milestone, evidence) -> ReleaseDecision: ...

class PaymentExecutionPort(Protocol):
    async def release(self, decision: ReleaseDecision) -> ExecutionReceipt: ...
```

Implementations:

- `KeeperHubPaymentExecutionAdapter` for the hackathon/stablecoin rail;
- existing iArtisanat payment-provider adapter for fiat/card/SEPA when available;
- `StubPaymentExecutionAdapter` for tests.

### API endpoints

- `POST /projects/{project_id}/payment-mandates`
- `POST /projects/{project_id}/milestones/{milestone_id}/evidence`
- `POST /projects/{project_id}/milestones/{milestone_id}/evaluate-release`
- `POST /projects/{project_id}/milestones/{milestone_id}/execute-release`
- `GET /projects/{project_id}/payment-audit`

### Non-negotiable product rules

- tenant isolation and existing RBAC;
- explicit client consent;
- human confirmation for configured thresholds;
- no raw wallet/private-key persistence;
- append-only audit events;
- idempotent execution;
- dispute freezes automated release;
- feature flag disabled by default;
- legal copy must call the feature a technical pilot, not a regulated escrow service.
