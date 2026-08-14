Known Issues (Deferred)

Purpose
Track confirmed discrepancies between spec and code that were
identified during the Postgres migration work but deliberately not
fixed in that session, to avoid losing context between chat sessions.
Two related issues from this same audit (webhook event not persisted
for unknown invoices; delivery failure mutating invoice state to
FAILED) were already fixed and verified by tests — not tracked here.

---

1. EXPIRED -> PAID transition is allowed in code

Where
app/domain/invoice/state_machine.py:
    InvoiceState.EXPIRED: {InvoiceState.PAID}
app/application/invoice/use_cases/mark_paid.py logs a warning
("Late payment accepted for invoice %s (was EXPIRED, now PAID)")
when this path is taken.

Spec conflict
invoice_state_machine.md lists EXPIRED -> PAID explicitly under
"Forbidden Transitions".

Status
Not a random bug — this is a deliberate feature ("late payment
accepted" pattern with logging), confirmed by the log message and
comment in mark_paid.py. Predates this session.

Risk
Real-money risk if this is unintentional: an expired invoice can be
paid later, possibly at a stale price (this interacts directly with
the BTCPay rate-lock question in btcpay_provider.md, where invoices
expire on a fixed rate window).

Decision needed
Either:
(a) keep the late-payment-accepted behavior and update
    invoice_state_machine.md to reflect it as an intentional
    exception (contradicts current spec wording), or
(b) remove the EXPIRED -> PAID transition and handle late payments
    via a separate reconciliation/refund flow instead.

Status: DEFERRED (decided 2026-08-08)
Keeping current behavior (EXPIRED -> PAID allowed) for now. Rationale:
CryptoBot (currency_conversion.md) converts fiat -> crypto at the
moment of payment, not at invoice creation, so a late CryptoBot
payment carries near-zero price risk. The real risk is BTCPay
(btcpay_provider.md), where the rate is locked at invoice creation
and held only for the expiration window — accepting a payment after
expiry there means honoring a stale rate, a genuine real-money risk
if BTC has moved.
This must be revisited BEFORE BTCPay goes live, not after. Once
BTCPay is implemented, either gate EXPIRED -> PAID to CryptoBot only,
or resolve per option (a)/(b) above for both providers.

---

2. REFUNDED state is entirely absent from the state machine

Where
app/domain/invoice/state_machine.py — InvoiceState enum only has
PENDING, PAID, DELIVERED, FAILED, EXPIRED. No REFUNDED.

Spec conflict
invoice_state_machine.md requires PAID -> REFUNDED as an allowed
transition. domain_model.md lists REFUNDED as one of five valid
Invoice statuses.

Risk
Refunds are currently architecturally impossible — there is no way
to represent a refunded invoice in the current schema/state machine.

Decision needed
Add REFUNDED to InvoiceState, add PAID -> REFUNDED transition, and
decide what (if anything) triggers it (manual admin action vs
provider refund webhook vs something else — not currently specified
anywhere).

Status: DEFERRED (decided 2026-08-08)
Explicitly deferred, not forgotten. Rationale: no provider contract
(CryptoBot or BTCPay) currently specifies a refund webhook, so the
only realistic near-term trigger would be a manual admin action
(e.g. an admin command), which is a real feature decision requiring
its own use-case design, not a small addition alongside the state
machine fix. Revisit once either (a) a provider refund webhook is
specified, or (b) manual refund becomes an actual product
requirement.

---

3. external_payment_id has no UNIQUE constraint

Where
app/infrastructure/database/models.py — Invoice.external_payment_id
is String(256), nullable=True, but not unique=True. No migration
adds a unique index either.

Spec conflict
domain_model.md Invoice Invariants: "external_payment_id must be
unique."

Risk
process_payment_event.py looks up the invoice via
get_by_external_payment_id() — if two invoices ever share the same
external_payment_id (e.g. a provider bug, or a race in invoice
creation), which one gets matched is undefined. Confirmed present in
the live Postgres schema during migration verification (\d invoices
showed no unique index on this column).

Decision needed
Add a migration for a unique constraint/index. Before doing so,
audit whether any existing dev data already violates it (not done
yet — dev DB was empty at time of writing, so this is safe to add
now if desired).

---

Already Fixed (for reference, not open)

- Webhook events for unknown external_payment_id were not persisted
  at all (violated webhook_idempotency.md's "every event must be
  stored" rule). Fixed in process_payment_event.py: PaymentEvent is
  now created and flushed before branching on invoice lookup.
  Required a migration (f3a1c9d47b62) to make PaymentEvent.invoice_id
  nullable. Verified by
  tests/test_payment_critical_paths.py::test_webhook_for_unknown_invoice_is_still_persisted.

- Delivery failure was mutating invoice.status to FAILED via
  InvoiceOps.mark_failed(), violating invoice_state_machine.md's
  "Delivery failure does NOT change invoice state." Fixed in
  deliver_invoice.py: failure now returns False without any state
  mutation, leaving the invoice in PAID so delivery can be retried.
  Verified by
  tests/test_payment_critical_paths.py::test_delivery_failure_does_not_change_invoice_state.

- process_payment_event.py ran PaymentEvent persistence, the PAID
  transition, and delivery inside a single UnitOfWork with one commit
  at the end. An unhandled exception during delivery (e.g. "Bot is
  not initialized") propagated out of the `async with UnitOfWork()`
  block, triggering a full rollback of the whole transaction — losing
  the just-created PaymentEvent and reverting PENDING -> PAID.
  Violated both webhook_idempotency.md ("every event must be stored")
  and invoice_state_machine.md ("Delivery failure does NOT change
  invoice state") simultaneously. Affected both providers equally
  (shared use-case, not BTCPay-specific) - surfaced during BTCPay
  end-to-end webhook testing on testnet with the bot intentionally
  not running. Fixed in process_payment_event.py: added a checkpoint
  commit immediately after MarkInvoicePaidUseCase, persisting the
  PaymentEvent and PAID transition before delivery is attempted;
  wrapped the delivery step in try/except so any exception - not
  just a returned False - is caught and recorded on
  event.last_error instead of propagating. Verified live against a
  real BTCPay testnet Settled webhook (paid_asset/paid_amount/
  paid_fiat_rate populated correctly, PaymentEvent persisted with
  processed=False, failed=True,
  last_error="delivery_exception: Bot is not initialized").
  No automated regression test yet - recommend adding one alongside
  test_payment_critical_paths.py before relying on this long-term.
