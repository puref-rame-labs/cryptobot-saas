BTCPay Server Provider

Purpose
Add BTCPay Server as a second payment provider alongside CryptoBot,
implementing a non-custodial settlement path: funds are paid directly
to a merchant-controlled wallet (on-chain BTC and/or Lightning),
with no third-party custodial balance involved.
No changes to domain invariants (Invoice/Product state machines stay
exactly as defined in invoice_state_machine.md and domain_model.md).
No changes to the provider contract itself
(payment_provider_contract.md) — BTCPay implements the same
create_invoice / verify_signature / normalize interface as any
other provider.

Scope
Applies to:
New BTCPay provider (app/application/payments/providers/btcpay/)
Provider configuration (app/config/settings.py)
Provider registry (app/application/payments/registry.py,
app/application/payments/providers/registry.py)
Invoice creation use-case (network resolution reused from the
CryptoBot mainnet/testnet pattern, see below)
Does NOT apply to:
Mock provider (unaffected, remains network-agnostic dev tool)
CryptoBot provider (unaffected, coexists as an independent provider)
Invoice/Product state machines
Webhook idempotency pipeline (algorithm unchanged, see below)

Non-Custodial Model
Unlike CryptoBot, BTCPay does not hold a custodial balance capable of
settling in multiple assets. Payment settles directly to the
merchant's configured wallet (xpub) on-chain, or via Lightning if
enabled on the BTCPay Store.
Consequence for Invoice fields (currency_conversion.md):
paid_asset is effectively constant for this provider (e.g. always
"BTC"), not a variable selected by the buyer as with CryptoBot.
paid_amount / paid_fiat_rate are still populated from the webhook
payload, same as any other provider — only the asset dimension is
narrower.
This is a provider-level characteristic, not a schema change:
Invoice fields stay as defined in currency_conversion.md and
domain_model.md.

Rate-Lock Semantics (Open Question — deferred)
BTCPay's default behavior differs from CryptoBot's:
CryptoBot (currency_conversion.md): fiat -> crypto rate stays
live until the moment of payment.
BTCPay: fiat -> BTC rate is fixed at invoice-creation time and
held only for the invoice's configured expiration window (BTCPay
default ~15-60 min). If payment arrives after expiration, BTCPay
treats the invoice as Expired/Invalid regardless of amount received.
This is NOT being resolved now. It is intentionally deferred:
paid_fiat_rate semantics are per-provider (rate-at-creation for
BTCPay vs rate-at-payment for CryptoBot) — this asymmetry is
accepted and documented, not normalized away.
Whether to widen BTCPay's invoice expiration window, add grace-period
handling for late payments, or leave BTCPay defaults as-is is
unresolved — see Open Questions.

Network Model: Mainnet + Per-Admin Testnet/Regtest Override
Mirrors the CryptoBot pattern (testnet_mainnet_migration.md) rather
than introducing a new mechanism:
Two separate credential/host pairs configured simultaneously:
BTCPAY_MAINNET_HOST / BTCPAY_MAINNET_API_KEY / BTCPAY_MAINNET_STORE_ID
BTCPAY_TESTNET_HOST / BTCPAY_TESTNET_API_KEY / BTCPAY_TESTNET_STORE_ID
(testnet host may point at a self-hosted BTCPay instance running
against Bitcoin testnet or regtest — exact topology to be confirmed
during rollout, see Rollout Plan)
Default network for all regular users is mainnet.
Admins (per existing is_admin filter) can opt into testnet for
their own invoice creation, reusing the same per-admin override
column added for CryptoBot (cadc800cbb81_add_testnet_override_to_users),
not a separate BTCPay-specific flag.
Network resolution happens per invoice-creation call, not globally,
identical logic to CryptoBot:
network = testnet if (is_admin(user) and admin_testnet_override_active) else mainnet.
The override is scoped to the requesting admin only — it MUST NOT
affect network selection for any other user's invoices, and MUST NOT
affect network selection for other providers' invoices.
Invoice.network (existing field, 24f90ba0d5a4_add_network_to_invoices)
is reused as-is — no new column needed. Provider + network together
identify which BTCPay host/store an invoice belongs to.

Invariants
Provider contract rules apply unchanged (payment_provider_contract.md):
BTCPay provider code MUST NOT access DB, perform delivery, or
enforce product state rules.
Idempotency key computation is unchanged (idempotency.md /
webhook_idempotency.md): provider + external_payment_id + event_type.
BTCPay's own event types (e.g. InvoiceSettled, InvoiceProcessing,
InvoiceExpired, InvoiceInvalid) are mapped in normalize() to the
same canonical PaymentEventDTO used by CryptoBot — no provider-specific
branching outside the provider module.
Switching provider MUST NOT change invoice state machine behavior
(invoice_state_machine.md) — transitions remain provider-agnostic.
Real-money errors (webhook signature failure, amount mismatch,
unexpected asset) MUST be logged, never silently dropped — same
project-wide payment safety rule as testnet_mainnet_migration.md.
Regular (non-admin) users are NEVER routed to BTCPay testnet/regtest —
no implicit fallback in either direction.

Webhook Handling
BTCPay signs webhooks with an HMAC-SHA256 signature derived from a
per-store webhook secret (distinct from the API key used for
create_invoice). verify_signature() for this provider validates
against that secret, not the API key.
Every webhook event is persisted regardless of validity, consistent
with webhook_idempotency.md's persistence rule.
Whether BTCPay webhooks land on the existing shared
app/api/routes/payment_webhook.py (provider dispatched by payload)
or a dedicated route is an implementation detail, not an invariant —
follow whatever the current CryptoBot route already does.
RESOLVED (2026-08-15): the existing shared payment_webhook.py route
is used, dispatching by provider_name in the URL path
(/webhook/payment/{provider_name}). Implemented and verified via
live end-to-end testnet testing.

Rollout Plan
Provision a BTCPay Store (or confirm access to an existing one) for
mainnet; obtain API key + webhook secret + store ID.
Decide and provision the testnet/regtest topology (self-hosted
instance vs BTCPay's public testnet, if any) — confirm before
wiring config, since this differs from CryptoBot's ready-made
@CryptoTestnetBot.
Add BTCPay credential settings (mainnet + testnet pairs) to
app/config/settings.py, store outside version control.
Implement BTCPay provider module: create_invoice, verify_signature,
normalize, registered alongside cryptobot/mock in the provider
registry.
Confirm normalize() mapping from BTCPay invoice events to canonical
PaymentEventDTO statuses (PAID / EXPIRED / FAILED equivalents).
Confirm per-admin testnet override (already implemented for
CryptoBot) correctly resolves network for BTCPay invoice creation
without any BTCPay-specific override logic.
Run a manual low-value end-to-end purchase on mainnet as an admin
with the override OFF before exposing BTCPay as a selectable
provider to regular users.
Monitor PaymentEvent failures/retries closely for the first batch
of real BTCPay transactions, paying particular attention to
Expired events caused by the rate-lock window (see above).

STATUS (2026-08-15): Steps 1-6 complete on testnet. BTCPay Server
deployed self-hosted on VPS (kernelhost, Debian 13, 4GB RAM/80GB
disk), pruned testnet node fully synced. BTCPayProvider implemented
(create_invoice, verify_signature, normalize with a payment-methods
follow-up call for paid_asset/paid_amount/paid_fiat_rate enrichment
on settled invoices). Verified end-to-end through the real Telegram
bot: /buy -> real BTCPay invoice -> real testnet payment via faucet
-> webhook delivered through a cloudflared tunnel -> signature
verified -> invoice marked PAID -> product delivered in Telegram.
An EXPIRED->PAID late-payment scenario was also observed live (see
known_issues.md item 1). Steps 7-8 (mainnet purchase, monitoring)
remain, pending mainnet Store provisioning.

RUB Rate Source (RESOLVED 2026-08-15)
Kraken (BTCPay's original default) does not quote BTC_RUB
(ERR_NO_RULE_MATCH) - likely reflects major Western exchanges
dropping RUB pairs. Confirmed working sources for BTC_RUB: bitpay,
yadio, freecurrencyrates, bitcoinkenya - all niche/aggregator
sources rather than major exchange order books, likely themselves
deriving the rate via BTC_USD x USD_RUB proxy conversion rather than
a direct RUB order book.
Decision: use BTCPay's built-in Fallback rate source feature (Store
Settings > Rates), NOT custom rate-rule scripting. Primary: bitpay
(already in use, confirmed reliable during testnet testing).
Fallback: freecurrencyrates. Avoids a single point of failure if the
primary source becomes unavailable (as happened previously with
Coinaverage's API discontinuation, per BTCPay's own FAQ) - invoice
creation would otherwise fail outright with no automatic recovery,
as was observed today when Kraken was still configured.

Open Questions (resolve before implementation)
Rate-lock handling: accept BTCPay's default expiration window as-is,
widen it, or add grace-period/manual-reconciliation handling for
payments that arrive late at the original rate? (explicitly deferred,
see Rate-Lock Semantics above)
Asset scope: RESOLVED (2026-08-15) — on-chain BTC only for mainnet
launch, no Lightning for now. Rationale: the VPS (4GB RAM) is already
running bitcoind + NBXplorer + Postgres + BTCPay + Tor concurrently;
a Lightning node (LND/CLN/Eclair) would add another persistent
daemon plus its own channel-state database, and Lightning also
requires ongoing inbound-liquidity management and specialized
channel-backup handling (SCB) beyond the wallet seed — operational
overhead judged not worth it on this VPS's headroom right now.
Revisit if/when the BTCPay stack moves to a larger or dedicated VPS.
Confirmed by real testnet testing (2026-08-15): the dust-threshold
error BTCPay returns for small on-chain amounts explicitly suggests
enabling Lightning — a known, accepted tradeoff of the on-chain-only
decision, not a bug to fix.
Testnet/regtest topology: RESOLVED (2026-08-15) — self-hosted BTCPay
instance on the same VPS as production, running against Bitcoin
testnet3 (not regtest), pruned node. Chosen over regtest because
testnet exercises realistic webhook timing, confirmations, and
signature verification against real network conditions, matching
the same testnet/mainnet split already used for CryptoBot.
Webhook route: RESOLVED (2026-08-15) — see Webhook Handling above.
