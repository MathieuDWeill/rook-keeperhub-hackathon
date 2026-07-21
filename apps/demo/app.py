import base64
import hashlib
import html
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import requests
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
STYLE_PATH = Path(__file__).resolve().parent / "styles/rook.css"
DEPLOYMENT_PATH = ROOT / "artifacts/deployment.json"
LIVE_PROOF_PATH = ROOT / "artifacts/live-proof.json"

GROSS_MINOR = 3_000_000_000
RETENTION_BPS = 500
RELEASED_MINOR = GROSS_MINOR * (10_000 - RETENTION_BPS) // 10_000
RETENTION_MINOR = GROSS_MINOR - RELEASED_MINOR

st.set_page_config(page_title="Rook", page_icon="R", layout="wide", initial_sidebar_state="collapsed")


def load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def load_css() -> None:
    if STYLE_PATH.is_file():
        st.markdown(f"<style>{STYLE_PATH.read_text()}</style>", unsafe_allow_html=True)


def digest(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def money(amount_minor: int) -> str:
    return f"{amount_minor / 1_000_000:,.0f} USDC"


def truncate_address(value: str) -> str:
    if not value or len(value) < 12:
        return value or "Not available"
    return f"{value[:6]}…{value[-4:]}"


def short_hash(value: str | None) -> str:
    if not value:
        return "Not returned"
    return f"{value[:10]}…{value[-8:]}"


def e(value: object) -> str:
    return html.escape(str(value))


def copy_button(label: str, value: str, key: str) -> None:
    st.components.v1.html(
        f"""
        <button
          title="Copy {e(label)}"
          onclick="navigator.clipboard.writeText('{e(value)}'); this.innerText='Copied'; setTimeout(() => this.innerText='{e(label)}', 1200);"
          style="
            border: 1px solid #e8dfd0;
            background: #fffdf8;
            color: #16211b;
            border-radius: 999px;
            font: 700 12px Inter, sans-serif;
            padding: 8px 12px;
            cursor: pointer;
          "
        >{e(label)}</button>
        """,
        height=42,
    )


def proof_execution(proof: dict) -> dict:
    execution = proof.get("execution")
    return execution if isinstance(execution, dict) else {}


def audit_fields(execution: dict) -> dict:
    raw = execution.get("raw") if isinstance(execution.get("raw"), dict) else {}
    status = raw.get("status") if isinstance(raw.get("status"), dict) else {}
    return {
        "status": execution.get("status") or status.get("status") or "Not returned",
        "execution_id": execution.get("execution_id") or status.get("executionId"),
        "tx_hash": execution.get("tx_hash") or status.get("transactionHash"),
        "explorer_url": execution.get("explorer_url") or status.get("transactionLink"),
        "gas": status.get("gasUsedWei") or "Not returned",
        "timestamp": status.get("completedAt") or status.get("createdAt") or "Not returned",
    }


def build_payload(deployment: dict, scenario: str) -> dict:
    accepted = scenario == "Approved payment"
    suffix = "approved" if accepted else "blocked"
    return {
        "project_id": str(uuid4()),
        "milestone_id": f"kitchen-renovation-phase-1-{suffix}",
        "amount_minor": GROSS_MINOR,
        "token": "USDC",
        "recipient": os.getenv("ARTISAN_ADDRESS") or deployment.get("artisan", "0x" + "1" * 40),
        "escrow_contract": os.getenv("ESCROW_CONTRACT_ADDRESS") or deployment.get("escrow", "0x" + "2" * 40),
        "client_accepted": accepted,
        "invoice_verified": True,
        "compliance_clear": True,
        "dispute_open": False,
        "retention_bps": RETENTION_BPS,
        "evidence": [
            {
                "kind": "signed_acceptance",
                "uri": "ipfs://rook-kitchen-acceptance",
                "sha256": digest(f"acceptance-{suffix}"),
                "verified": accepted,
            },
            {
                "kind": "invoice",
                "uri": "ipfs://rook-kitchen-invoice",
                "sha256": digest(f"invoice-{suffix}"),
                "verified": True,
            },
            {
                "kind": "photo",
                "uri": "ipfs://rook-kitchen-photos",
                "sha256": digest(f"photos-{suffix}"),
                "verified": True,
            },
            {
                "kind": "compliance_document",
                "uri": "ipfs://rook-compliance",
                "sha256": digest(f"compliance-{suffix}"),
                "verified": True,
            },
        ],
    }


def render_header(mode: str) -> None:
    logo = ROOT / "assets/rook-logo.svg"
    logo_src = base64.b64encode(logo.read_bytes()).decode()
    st.markdown(
        f"""
        <div class="rook-header">
          <div class="rook-logo">
            <img src="data:image/svg+xml;base64,{logo_src}" alt="Rook logo" />
            <div class="rook-title">
              <h1>Rook</h1>
              <p>Secure milestone payments for construction</p>
            </div>
          </div>
          <div class="rook-badges">
            <span class="badge badge-live">{'LIVE' if mode == 'live' else 'STUB'} · KeeperHub</span>
            <span class="badge badge-net">Sepolia</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero(deployment: dict, payload: dict) -> None:
    artisan = payload["recipient"]
    escrow = payload["escrow_contract"]
    st.markdown(
        f"""
        <section class="hero">
          <div class="hero-top">
            <div>
              <div class="eyebrow">Milestone</div>
              <h2>Kitchen renovation — Phase 1</h2>
              <p class="hero-sub">A deterministic payment release: verified evidence, policy approval, then KeeperHub execution on Sepolia.</p>
            </div>
            <div class="address-stack">
              <div class="address-row">
                <span class="address-label">Artisan wallet</span>
                <span class="address-value" title="{e(artisan)}">{e(truncate_address(artisan))}</span>
              </div>
              <div class="address-row">
                <span class="address-label">Escrow contract</span>
                <span class="address-value" title="{e(escrow)}">{e(truncate_address(escrow))}</span>
              </div>
            </div>
          </div>
          <div class="metric-grid">
            <div class="metric-card"><span>Total</span><strong>{money(GROSS_MINOR)}</strong></div>
            <div class="metric-card"><span>Released today</span><strong>{money(RELEASED_MINOR)}</strong></div>
            <div class="metric-card"><span>Retention protected</span><strong>{money(RETENTION_MINOR)}</strong></div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    copy_cols = st.columns([1, 1, 5])
    with copy_cols[0]:
        copy_button("Copy escrow", escrow, "copy-escrow")
    with copy_cols[1]:
        copy_button("Copy artisan", artisan, "copy-artisan")


def render_timeline(state: str) -> None:
    steps = [
        ("01", "Evidence verified", "Acceptance, invoice and site evidence are present."),
        ("02", "Policy approved", "Retention and safety checks pass deterministically."),
        ("03", "Payment executed", "KeeperHub provides the execution audit trail."),
    ]
    markup = ['<div class="timeline">']
    for icon, title, copy in steps:
        markup.append(
            f'<div class="timeline-step"><div class="step-icon">{icon}</div>'
            f"<h3>{title}</h3><p>{copy}</p></div>"
        )
    markup.append("</div>")
    st.markdown("".join(markup), unsafe_allow_html=True)


def render_evidence() -> None:
    cards = [
        ("Client acceptance", "verified"),
        ("Invoice", "verified"),
        ("Compliance", "clear"),
        ("Dispute", "none"),
        ("Completion photos", "4 uploaded"),
    ]
    st.markdown(
        '<div class="panel"><h3>Evidence</h3><div class="evidence-grid">'
        + "".join(
            f'<div class="evidence-card"><span>{label}</span><strong>{value}</strong></div>'
            for label, value in cards
        )
        + "</div></div>",
        unsafe_allow_html=True,
    )


def render_policy() -> None:
    st.markdown(
        f"""
        <div class="panel">
          <h3>Payment policy</h3>
          <div class="policy-line"><span>Gross amount</span><strong>{money(GROSS_MINOR)}</strong></div>
          <div class="policy-line"><span>Retention</span><strong>5%</strong></div>
          <div class="policy-line"><span>Payable now</span><strong>{money(RELEASED_MINOR)}</strong></div>
          <div class="policy-line"><span>Release condition</span><strong>all checks passed</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_success(execution: dict, title: str = "Payment executed through KeeperHub") -> None:
    fields = audit_fields(execution)
    explorer = fields["explorer_url"]
    timestamp = fields["timestamp"]
    if timestamp == "Not returned" and execution:
        timestamp = datetime.now(timezone.utc).isoformat()
    st.markdown(
        f"""
        <div class="success-card">
          <div class="success-heading">
            <span class="success-dot"></span>
            <h3>{e(title)}</h3>
          </div>
          <div class="audit-line"><span>Transaction hash</span><strong title="{e(fields['tx_hash'])}">{e(short_hash(fields['tx_hash']))}</strong></div>
          <div class="audit-line"><span>Execution ID</span><strong>{e(fields['execution_id'] or 'Not returned')}</strong></div>
          <div class="audit-line"><span>Gas used</span><strong>{e(fields['gas'])}</strong></div>
          <div class="audit-line"><span>Timestamp</span><strong>{e(timestamp)}</strong></div>
          <div class="audit-line"><span>Audit status</span><strong>{e(fields['status'])}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    controls = st.columns([1, 1, 4])
    if explorer and explorer != "Not returned":
        with controls[0]:
            st.link_button("View on explorer", explorer, use_container_width=True)
    if fields["tx_hash"]:
        with controls[1]:
            copy_button("Copy hash", fields["tx_hash"], "copy-hash")


def render_blocked(reasons: list[str] | None = None) -> None:
    reason = "client acceptance missing"
    if reasons:
        reason = reasons[0].lower()
    st.markdown(
        f"""
        <div class="blocked-card">
          <h3>Payment safely blocked</h3>
          <p>Rook refused the release before KeeperHub execution — {e(reason)}.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def call_api(path: str, payload: dict, timeout: int = 120) -> dict:
    response = requests.post(f"{api}{path}", json=payload, timeout=timeout)
    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(response.text[:500]) from exc
    if response.status_code >= 400:
        detail = data.get("detail") if isinstance(data, dict) else response.text
        raise RuntimeError(str(detail))
    return data


load_css()
deployment = load_json(DEPLOYMENT_PATH)
stored_proof = load_json(LIVE_PROOF_PATH)
api = os.getenv("API_BASE_URL", "http://localhost:8000")
mode = os.getenv("KEEPERHUB_MODE", "stub").lower()

with st.sidebar:
    st.markdown("### Demo scenario")
    scenario = st.radio(
        "Scenario",
        ["Approved payment", "Blocked payment"],
        label_visibility="collapsed",
    )
    technical_mode = st.toggle("Technical mode", value=False)
    st.caption("No manual contract addresses are required after deployment.")

payload = build_payload(deployment, scenario)
render_header(mode)
render_hero(deployment, payload)
render_timeline("ready")

left, right = st.columns([1.12, 0.88])
with left:
    render_evidence()
with right:
    render_policy()

st.write("")
actions = st.columns([0.52, 0.28, 0.20])
with actions[0]:
    approve_clicked = st.button(
        f"Approve and execute {money(RELEASED_MINOR)}",
        type="primary",
        use_container_width=True,
        disabled=scenario != "Approved payment",
        help="Runs policy validation, KeeperHub simulation, then on-chain execution in live mode.",
    )
with actions[1]:
    blocked_clicked = st.button(
        "Test blocked payment",
        use_container_width=True,
        help="Runs the same flow without client acceptance and confirms no payment is executed.",
    )

result = st.session_state.get("result")
try:
    if approve_clicked:
        with st.spinner("KeeperHub simulation, policy validation and on-chain execution are running..."):
            time.sleep(0.35)
            result = call_api("/v1/releases/execute", payload)
            st.session_state["result"] = result
            st.session_state["result_kind"] = "approved"
    if blocked_clicked or (scenario == "Blocked payment" and st.session_state.get("auto_blocked") is None):
        blocked_payload = build_payload(deployment, "Blocked payment")
        with st.spinner("Validating blocked-payment policy..."):
            result = call_api("/v1/releases/execute", blocked_payload, timeout=30)
            st.session_state["result"] = result
            st.session_state["result_kind"] = "blocked"
            st.session_state["auto_blocked"] = True
except (requests.RequestException, RuntimeError) as exc:
    st.error(f"Execution error: {exc}")

result_kind = st.session_state.get("result_kind")
if result:
    decision = result.get("decision") or {}
    execution = result.get("execution") or {}
    if result_kind == "blocked" or decision.get("status") == "rejected":
        render_blocked(decision.get("reasons") or [])
    elif execution:
        render_success(execution)
elif proof_execution(stored_proof):
    render_success(proof_execution(stored_proof), title="Existing live KeeperHub proof")

if technical_mode:
    with st.expander("Technical details", expanded=False):
        st.markdown('<p class="technical-note">Raw payload and audit records are hidden during the main demo.</p>', unsafe_allow_html=True)
        st.write("Request payload")
        st.json(payload)
        if result:
            st.write("Latest API response")
            st.json(result)
        elif stored_proof:
            st.write("Stored live proof")
            st.json(stored_proof)
