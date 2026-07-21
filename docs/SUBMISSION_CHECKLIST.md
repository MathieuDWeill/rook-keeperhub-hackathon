# Submission checklist

## Mandatory

- [x] Public GitHub repository: `https://github.com/MathieuDWeill/rook-keeperhub-hackathon`
- [ ] Demo video: `________________`
- [ ] KeeperHub-executed transaction: `________________`
- [ ] Transaction hash saved in `artifacts/final-transaction.txt`
- [ ] README contains final links
- [ ] No `.env`, key, wallet file or secret committed

## Technical proof

- [ ] `make check` passes
- [ ] `artifacts/deployment.json` exists
- [ ] Live UI shows KeeperHub simulation
- [ ] Live UI shows execution ID
- [ ] Live UI shows authoritative transaction link
- [ ] Missing client acceptance causes policy rejection and no execution
- [ ] Reusing the same immutable decision cannot double-pay onchain

## DoraHacks copy

**Name:** Rook

**Tagline:** Evidence-gated construction payments executed reliably through KeeperHub.

**One-liner:** Clients fund once; artisans are paid when signed evidence and compliance checks satisfy a deterministic policy, with retention and a complete KeeperHub execution trail.
