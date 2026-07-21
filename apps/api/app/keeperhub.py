from __future__ import annotations

import asyncio
import json
import os
from typing import Any

import httpx

from .models import ExecutionResult, PolicyDecision, ReleaseRequest


class KeeperHubError(RuntimeError):
    """Raised when KeeperHub rejects or cannot complete an execution."""


ROOK_RELEASE_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "decisionId", "type": "bytes32"},
            {"internalType": "bytes32", "name": "milestoneId", "type": "bytes32"},
            {"internalType": "address", "name": "recipient", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "release",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]


class KeeperHubExecutor:
    """Official KeeperHub Direct Execution adapter.

    Safety sequence:
    1. dry-run the exact contract call;
    2. only broadcast if simulation succeeds and wouldRevert is false;
    3. send an Idempotency-Key derived from the immutable decision id;
    4. fetch the authoritative status/transaction link.
    """

    def __init__(self) -> None:
        self.mode = os.getenv("KEEPERHUB_MODE", "stub").lower()
        self.base_url = os.getenv("KEEPERHUB_BASE_URL", "https://app.keeperhub.com").rstrip("/")
        self.api_key = os.getenv("KEEPERHUB_API_KEY", "")
        self.chain_id = int(os.getenv("CHAIN_ID", "11155111"))
        self.timeout = float(os.getenv("KEEPERHUB_TIMEOUT_SECONDS", "90"))
        self.max_polls = int(os.getenv("KEEPERHUB_MAX_POLLS", "12"))

    async def execute_release(
        self, request: ReleaseRequest, decision: PolicyDecision
    ) -> ExecutionResult:
        if decision.status != "approved":
            raise KeeperHubError("Rejected policy decisions cannot be executed")

        payload = self._contract_call_payload(request, decision)
        if self.mode != "live":
            return ExecutionResult(
                mode="stub",
                status="not_submitted",
                simulation={
                    "success": True,
                    "status": "local_stub",
                    "wouldRevert": False,
                    "notice": "No KeeperHub request or on-chain transaction was made",
                },
                raw={"keeperhub_contract_call": payload},
            )

        if not self.api_key.startswith("kh_"):
            raise KeeperHubError("Live mode requires an organisation-scoped KEEPERHUB_API_KEY (kh_…)")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Request-Id": f"rook-{decision.decision_id}",
        }
        endpoint = f"{self.base_url}/api/execute/contract-call"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            simulation_response = await client.post(
                endpoint,
                headers=headers,
                json={**payload, "simulate": True},
            )
            simulation = self._json_or_error(simulation_response, "simulation")
            if simulation_response.is_error or not simulation.get("success") or simulation.get(
                "wouldRevert", True
            ):
                reason = simulation.get("revertReason") or simulation.get("error") or simulation
                raise KeeperHubError(f"KeeperHub simulation blocked execution: {reason}")

            broadcast_headers = {
                **headers,
                "Idempotency-Key": f"rook-release-{decision.decision_id}",
            }
            execution_response = await client.post(
                endpoint,
                headers=broadcast_headers,
                json=payload,
            )
            execution = self._json_or_error(execution_response, "broadcast")
            if execution_response.is_error:
                raise KeeperHubError(
                    f"KeeperHub broadcast failed ({execution_response.status_code}): {execution}"
                )

            execution_id = execution.get("executionId")
            if not execution_id:
                raise KeeperHubError(f"KeeperHub returned no executionId: {execution}")

            status = await self._get_terminal_status(client, headers, str(execution_id))

        tx_hash = status.get("transactionHash")
        explorer_url = status.get("transactionLink")
        final_status = str(status.get("status", execution.get("status", "submitted")))
        if final_status == "failed":
            raise KeeperHubError(f"KeeperHub execution failed: {status.get('error') or status}")

        return ExecutionResult(
            mode="live",
            status=final_status,
            execution_id=str(execution_id),
            tx_hash=str(tx_hash) if tx_hash else None,
            explorer_url=str(explorer_url) if explorer_url else None,
            simulation=simulation,
            raw={"broadcast": execution, "status": status},
        )

    async def _get_terminal_status(
        self, client: httpx.AsyncClient, headers: dict[str, str], execution_id: str
    ) -> dict[str, Any]:
        last: dict[str, Any] = {}
        url = f"{self.base_url}/api/execute/{execution_id}/status"
        for _ in range(self.max_polls):
            response = await client.get(url, headers=headers)
            last = self._json_or_error(response, "status")
            if response.is_error:
                raise KeeperHubError(f"KeeperHub status lookup failed: {last}")
            if last.get("status") in {"completed", "failed"}:
                return last
            hint = response.headers.get("X-Poll-Interval-Hint", "2")
            try:
                delay = max(0.25, min(float(hint), 10.0))
            except ValueError:
                delay = 2.0
            await asyncio.sleep(delay)
        return last

    def _contract_call_payload(
        self, request: ReleaseRequest, decision: PolicyDecision
    ) -> dict[str, Any]:
        return {
            "contractAddress": request.escrow_contract,
            "chainId": self.chain_id,
            "functionName": "release",
            "functionArgs": json.dumps(
                [
                    self._uuid_to_bytes32(str(decision.decision_id)),
                    self._text_to_bytes32(request.milestone_id),
                    request.recipient,
                    str(decision.releasable_amount_minor),
                ]
            ),
            "abi": json.dumps(ROOK_RELEASE_ABI, separators=(",", ":")),
            "gasLimitMultiplier": os.getenv("KEEPERHUB_GAS_LIMIT_MULTIPLIER", "1.2"),
        }

    @staticmethod
    def _uuid_to_bytes32(value: str) -> str:
        return "0x" + value.replace("-", "").lower().rjust(64, "0")

    @staticmethod
    def _text_to_bytes32(value: str) -> str:
        # Ethereum keccak is generated by the contract tooling in production; for the
        # API payload we use the deterministic 32-byte UTF-8 representation when it fits.
        encoded = value.encode("utf-8")
        if len(encoded) > 32:
            raise KeeperHubError("milestone_id must fit in bytes32 (32 UTF-8 bytes max)")
        return "0x" + encoded.hex().ljust(64, "0")

    @staticmethod
    def _json_or_error(response: httpx.Response, phase: str) -> dict[str, Any]:
        try:
            data = response.json()
            return data if isinstance(data, dict) else {"data": data}
        except ValueError:
            return {
                "error": f"non_json_{phase}_response",
                "status_code": response.status_code,
                "body": response.text[:1000],
            }
