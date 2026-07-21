# Prompt Codex — integrate Rook into the existing iArtisanat repository

You are working in the existing iArtisanat repository. A separate hackathon scaffold named `Rook` is available beside this repository or as an extracted folder. Your task is to integrate its **secure milestone payment capability** into iArtisanat without importing the hackathon demo UI or weakening the existing architecture.

## Objective

Add a feature-flagged `Secure Payments` module that supports:

1. creation of a payment mandate from an accepted quote;
2. project milestones and retention percentage;
3. evidence attachment using the existing document vault/timeline infrastructure;
4. deterministic release evaluation;
5. optional execution through a `KeeperHubPaymentExecutionAdapter`;
6. append-only audit history;
7. freeze on dispute;
8. idempotent retries.

## Source material

Read first:

- `Rook/docs/IARTISANAT_INTEGRATION.md`
- `Rook/apps/api/app/models.py`
- `Rook/apps/api/app/policy.py`
- `Rook/apps/api/app/keeperhub.py`
- `Rook/contracts/contracts/RookEscrow.sol`

Treat these as a reference implementation, not code that must be copied literally.

## Repository-first procedure

1. Inspect the iArtisanat architecture, frameworks, database conventions, migrations, services, API style, auth, RBAC, event/audit model, test stack and frontend patterns.
2. Reuse existing project, quote, invoice, document, timeline, tenant and user entities where appropriate.
3. Produce `docs/secure-payments-design.md` describing the chosen design and mapping from Rook concepts to existing iArtisanat concepts.
4. Implement the smallest coherent vertical slice end-to-end.

## Required domain model

Use names idiomatic to the existing codebase, covering at least:

- payment mandate;
- milestone;
- evidence reference;
- release decision;
- execution attempt/receipt;
- dispute/freeze state;
- retention.

Store monetary values as integers/Decimals according to the repository convention, never binary floats.

## Required interfaces

Create a provider-neutral execution port and at least two adapters:

- `StubPaymentExecutionAdapter` for deterministic tests;
- `KeeperHubPaymentExecutionAdapter`, entirely configured through environment variables and disabled unless the feature flag is enabled.

No business service may call KeeperHub directly.

## Policy invariants

- an LLM may classify or summarize evidence but cannot approve payment by itself;
- missing signed acceptance blocks release;
- missing verified invoice blocks release;
- open dispute blocks release;
- configured compliance failure blocks release;
- retention is calculated deterministically;
- a rejected decision cannot be executed;
- every approved decision has a unique idempotency key;
- retries cannot duplicate a payment;
- no private key is stored by iArtisanat.

## API/UI

Implement endpoints and UI consistent with the existing product, enabling an authorized organization user to:

- create or inspect a mandate from a quote/project;
- define milestones;
- attach existing vault documents as evidence;
- evaluate a milestone;
- confirm execution when required;
- inspect the complete audit timeline.

Add a clear badge for `Simulation`, `Awaiting confirmation`, `Submitted`, `Confirmed`, `Rejected`, and `Frozen`.

## Security and tenancy

- preserve tenant isolation;
- use existing RBAC and add the narrowest permissions needed;
- sensitive execution must require owner/admin or an explicit new permission;
- validate all external addresses, amounts and provider responses;
- redact provider secrets from logs;
- add rate limiting or reuse existing protections;
- use an outbox/job pattern if the repository already has one.

## Feature flags and configuration

Add documented configuration equivalent to:

- `SECURE_PAYMENTS_ENABLED=false`
- `PAYMENT_EXECUTION_PROVIDER=stub`
- `KEEPERHUB_BASE_URL`
- `KEEPERHUB_API_KEY`
- `KEEPERHUB_WORKFLOW_ID`
- `KEEPERHUB_EXECUTE_PATH`
- `BLOCK_EXPLORER_TX_BASE`

The application must start safely when none of the KeeperHub values are present.

## Tests

Add unit, API/service and relevant frontend tests covering:

- successful evaluation with retention;
- rejection without acceptance;
- rejection with dispute;
- unauthorized cross-tenant access;
- idempotent duplicate execution;
- provider timeout and retry;
- stub mode never claiming a real transaction;
- audit event creation.

Run the full existing test/lint/typecheck/build suite, not only new tests. Fix only regressions caused by this work. Do not perform unrelated refactors.

## Deliverables

- working code in the iArtisanat repository;
- migration(s);
- tests;
- `.env.example` updates;
- product documentation;
- `docs/secure-payments-design.md`;
- a final summary listing changed files, commands run, test results, remaining live KeeperHub setup, and any legal/product caveats.

Do not claim that iArtisanat is a regulated escrow provider. Label this as a technical pilot until a licensed payment/escrow partner and legal validation are in place.
