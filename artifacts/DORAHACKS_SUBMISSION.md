# Rook

**Evidence-gated construction payments executed reliably through KeeperHub.**

## One-line description
Rook releases construction milestone payments only after deterministic evidence and compliance checks pass, then uses KeeperHub to simulate, execute and audit the onchain settlement.

## Problem
Construction clients fear paying before work is accepted; artisans lose cash flow while funds and evidence are disputed. Existing workflows scatter acceptance, invoice, compliance and payment across emails, PDFs and bank transfers.

## Solution
Rook turns evidence into a payment mandate. Unsafe mandates stop before any blockchain call. Approved mandates are simulated and broadcast through KeeperHub with idempotency and an authoritative transaction trail.

## KeeperHub usage
- Direct Execution API contract call
- identical simulation-before-broadcast payload
- organization API key authentication
- idempotency key per deterministic decision
- status polling with KeeperHub interval hints
- transaction hash and explorer link as proof

## Links
- Source: <ADD_GITHUB_URL>
- Demo video: <ADD_VIDEO_URL>
- KeeperHub transaction: <ADD_KEEPERHUB_TRANSACTION_URL>
- Escrow contract: `<ADD_ESCROW_ADDRESS>`

## Commercial path
The module becomes **iArtisanat Secure Payments**, sold as a recurring add-on and transaction service for artisans, construction marketplaces and financing partners.
