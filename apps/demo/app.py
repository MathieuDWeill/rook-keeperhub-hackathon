import hashlib
import os

import requests
import streamlit as st

st.set_page_config(page_title="Rook", page_icon="🛡️", layout="wide")
st.title("Rook")
st.caption("Evidence-gated construction payments, executed reliably through KeeperHub")

api = os.getenv("API_BASE_URL", "http://localhost:8000")
default_recipient = os.getenv("ARTISAN_ADDRESS", "0x" + "1" * 40)
default_contract = os.getenv("ESCROW_CONTRACT_ADDRESS", "0x" + "2" * 40)
mode = os.getenv("KEEPERHUB_MODE", "stub").lower()


def digest(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


with st.sidebar:
    st.header("Execution")
    st.metric("KeeperHub mode", mode.upper())
    if mode == "live":
        st.success("Real simulation and on-chain execution enabled")
    else:
        st.warning("Safe stub: no transaction will be submitted")
    contract = st.text_input("Escrow contract", value=default_contract)
    recipient = st.text_input("Artisan wallet", value=default_recipient)
    st.divider()
    st.header("Milestone")
    amount = st.number_input("Gross amount (USDC)", min_value=1.0, value=3000.0, step=100.0)
    retention = st.slider("Retention (%)", 0, 20, 5)
    accepted = st.checkbox("Client signed acceptance", value=True)
    invoice = st.checkbox("Invoice verified", value=True)
    compliance = st.checkbox("Compliance clear", value=True)
    dispute = st.checkbox("Open dispute", value=False)

payload = {
    "milestone_id": "milestone-1",
    "amount_minor": int(amount * 1_000_000),
    "token": "USDC",
    "recipient": recipient,
    "escrow_contract": contract,
    "client_accepted": accepted,
    "invoice_verified": invoice,
    "compliance_clear": compliance,
    "dispute_open": dispute,
    "retention_bps": retention * 100,
    "evidence": [
        {
            "kind": "signed_acceptance",
            "uri": "ipfs://demo-acceptance",
            "sha256": digest("acceptance"),
            "verified": accepted,
        },
        {
            "kind": "invoice",
            "uri": "ipfs://demo-invoice",
            "sha256": digest("invoice"),
            "verified": invoice,
        },
        {
            "kind": "photo",
            "uri": "ipfs://demo-photo",
            "sha256": digest("photo"),
            "verified": True,
        },
    ],
}

kpi1, kpi2, kpi3 = st.columns(3)
retained = int(payload["amount_minor"] * payload["retention_bps"] / 10_000)
kpi1.metric("Gross milestone", f"{amount:,.2f} USDC")
kpi2.metric("Released now", f"{(payload['amount_minor'] - retained) / 1_000_000:,.2f} USDC")
kpi3.metric("Protected retention", f"{retained / 1_000_000:,.2f} USDC")

left, right = st.columns([1, 1])
with left:
    st.subheader("1. Evidence mandate")
    st.json(payload)
with right:
    st.subheader("2. Policy and execution")
    evaluate_clicked = st.button("Evaluate policy", use_container_width=True)
    execute_clicked = st.button(
        "Execute through KeeperHub",
        type="primary",
        use_container_width=True,
        help="In live mode this first simulates, then broadcasts with idempotency protection.",
    )
    try:
        if evaluate_clicked:
            response = requests.post(f"{api}/v1/releases/evaluate", json=payload, timeout=20)
            response.raise_for_status()
            st.session_state["result"] = response.json()
        if execute_clicked:
            response = requests.post(f"{api}/v1/releases/execute", json=payload, timeout=120)
            if response.status_code >= 400:
                detail = response.json().get("detail", response.text)
                st.error(detail)
            else:
                st.session_state["result"] = response.json()
    except requests.RequestException as exc:
        st.error(f"API unavailable: {exc}")

    result = st.session_state.get("result")
    if result:
        decision = result["decision"]
        if decision["status"] == "approved":
            st.success("POLICY APPROVED")
        else:
            st.error("POLICY REJECTED")
        for reason in decision["reasons"]:
            st.write(f"• {reason}")

        execution = result.get("execution") or {}
        if execution:
            st.subheader("KeeperHub audit")
            simulation = execution.get("simulation") or {}
            if simulation:
                st.write("**Simulation**")
                st.json(simulation)
            st.write(f"**Execution status:** `{execution.get('status')}`")
            if execution.get("execution_id"):
                st.code(execution["execution_id"], language=None)
            if execution.get("tx_hash"):
                st.code(execution["tx_hash"], language=None)
            if execution.get("explorer_url"):
                st.link_button("Open verified transaction", execution["explorer_url"])
            with st.expander("Raw execution record"):
                st.json(execution.get("raw", {}))

st.divider()
st.markdown(
    "**Judge test:** uncheck ‘Client signed acceptance’ and execute again. "
    "Rook rejects the release before KeeperHub is called."
)
