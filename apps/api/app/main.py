from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .keeperhub import KeeperHubError, KeeperHubExecutor
from .models import DecisionStatus, ReleaseRequest, ReleaseResponse
from .policy import evaluate_release

app = FastAPI(
    title="Rook API",
    version="0.2.0",
    description="Policy-gated construction milestone releases executed through KeeperHub.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "rook"}


@app.post("/v1/releases/evaluate", response_model=ReleaseResponse)
def evaluate(request: ReleaseRequest) -> ReleaseResponse:
    return ReleaseResponse(request=request, decision=evaluate_release(request))


@app.post("/v1/releases/execute", response_model=ReleaseResponse)
async def execute(request: ReleaseRequest) -> ReleaseResponse:
    decision = evaluate_release(request)
    if decision.status == DecisionStatus.REJECTED:
        return ReleaseResponse(request=request, decision=decision)
    try:
        # Instantiate per request so changed .env values are picked up during local demos.
        execution = await KeeperHubExecutor().execute_release(request, decision)
    except KeeperHubError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ReleaseResponse(request=request, decision=decision, execution=execution)
