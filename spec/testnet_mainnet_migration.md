Testnet → Mainnet Migration
Purpose
Switch the CryptoBot payment provider from testnet to mainnet so that
invoices are settled with real cryptocurrency instead of test assets,
while keeping testnet available on-demand for admin verification.
No changes to domain invariants (Invoice/Product state machines stay
exactly as defined in invoice_state_machine.md and
domain_model.md).
Scope
Applies to:
CryptoBot provider (app/application/payments/providers/cryptobot/)
Provider configuration (app/config/settings.py)
Invoice creation use-case (network resolution added as a new input)
Does NOT apply to:
Mock provider (unaffected, remains network-agnostic dev tool)
Invoice/Product state machines
Webhook idempotency pipeline
Network Model: Default Mainnet + Per-Admin Testnet Override
CryptoBot testnet and mainnet are separate applications with
independent API tokens and hosts (@CryptoBot /
pay.crypt.bot for mainnet vs @CryptoTestnetBot /
testnet-pay.crypt.bot for testnet). Both credential pairs MUST be
configured simultaneously — this is not a single-flag swap.
Config holds both pairs at once:
CRYPTOBOT_MAINNET_TOKEN / CRYPTOBOT_MAINNET_HOST
CRYPTOBOT_TESTNET_TOKEN / CRYPTOBOT_TESTNET_HOST
Default network for all regular users is mainnet.
Admins (per existing is_admin filter) can opt into testnet for
their own invoice creation, to verify the flow without risking
real funds.
Network resolution happens per invoice-creation call, not globally:
network = testnet if (is_admin(user) and admin_testnet_override_active) else mainnet.
The override is scoped to the requesting admin only — it MUST NOT
affect network selection for any other user's invoices.
Invariants
Switching network MUST NOT change invoice state machine behavior
(see invoice_state_machine.md — transitions are network-agnostic).
Switching network MUST NOT alter the idempotency algorithm
(webhook_idempotency.md) — key computation stays
provider + external_payment_id + event_type.
Regular (non-admin) users are NEVER routed to testnet — no implicit
fallback in either direction.
Invoice MUST record which network it was created on (new field,
e.g. network: "mainnet" | "testnet"), since testnet and mainnet
invoices coexist in the same table going forward.
Existing pre-migration testnet invoices/data are NOT retroactively
tagged — this field applies only to invoices created after rollout
(same precedent as currency_conversion.md's note on test
products).
Real-money errors (webhook signature failure, amount mismatch,
unexpected asset) MUST be logged, never silently dropped —
consistent with existing project-wide payment safety rule.
Rollback is config-only: reverting CRYPTOBOT_MAINNET_* /
disabling mainnet routing MUST be sufficient to stop real-money
invoice creation, with no separate maintenance-mode code path
required.
Rollout Plan
Provision mainnet API token via @CryptoBot, confirm mainnet host
(pay.crypt.bot), store both outside version control.
Add network column to Invoice (Alembic migration,
render_as_batch=True).
Confirm current supported-asset list and minimum invoice amount
for mainnet via getCurrencies/getExchangeRates against the
live mainnet host — asset availability (e.g. ETH) has changed
over time per CryptoBot's own changelog, don't assume parity with
testnet.
Implement per-admin testnet override (toggle command or setting,
checked at invoice-creation time via is_admin).
Confirm verify_signature() / normalize() behave identically
against mainnet webhook payloads.
Run a manual low-value end-to-end purchase on mainnet as an admin
with the override OFF (i.e. actually hitting mainnet) before
opening to all users.
Enable mainnet as default; monitor PaymentEvent failures/retries
closely for the first batch of real transactions.
Open Questions (resolve before implementation)
Should the per-admin testnet override be a persistent per-admin
setting (stored, sticky across sessions) or a one-shot flag per
/buy invocation? Affects whether it needs a DB column vs FSM
state only.
Exact current minimum invoice amount and accepted asset list on
mainnet — must be pulled live from the API right before rollout,
not hardcoded from docs (see step 3 above).
