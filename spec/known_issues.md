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

Status: RESOLVED (decided 2026-08-08, formalized 2026-08-15)
Option (a) chosen. Formal rationale and volatility-based risk
estimate now live in invoice_state_machine.md under "Intentional
Exception: EXPIRED → PAID (late payment)" instead of being deferred
here - see that spec for the full decision record.

Original deferred rationale, preserved for history:
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

Live example observed (2026-08-15): during BTCPay end-to-end testnet
testing, invoice #8 (5000 RUB, rate locked at creation via bitpay
BTC_RUB) expired while webhook delivery was blocked by a cloudflared
tunnel connectivity issue (see new Operational Notes entry below).
When the webhook finally landed, mark_paid.py logged "Late payment
accepted for invoice 8 (was EXPIRED, now PAID, tx_hash=None)" and
the invoice was honored at the original locked rate. This is the
exact real-money scenario this issue warns about — now confirmed
reproducible in practice, not just theoretical. Reinforces: resolve
before mainnet.

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

Note (2026-08-16): REFUNDED design is intentionally sequenced AFTER
the referral program use-case (see project architecture notes -
ReferralAccrual ledger, referred_by_id/referral_code on User). Abuse
vector identified: without REFUNDED being aware of referral accrual,
a self-referral (or colluding accounts) could purchase to trigger a
referral payout, then refund the purchase while keeping the accrued
bonus - the refund and the accrual must be part of the same
idempotent transaction, not designed independently. REFUNDED state
machine work should treat ReferralAccrual reversal as a first-class
requirement, not a follow-up patch.

Update (2026-08-17): Referral program implemented per referral_program.md
(migration b3f7a19c2d05_add_referral_program - User.referral_code,
User.referred_by_id, ReferralAccrual table with a unique constraint on
invoice_id). Accrual is created inside the same idempotent checkpoint
as the PAID transition in process_payment_event.py, before delivery -
verified by
tests/test_payment_critical_paths.py::test_referral_accrual_created_once_on_paid_and_survives_replay,
which confirms a replayed webhook does not create a duplicate accrual.
Payout is manual-only for v1 (/referral_payouts, admin-gated), no
CryptoBot Transfer API integration - see referral_program.md "Payout
(Manual, v1)".

The sequencing precondition noted above (2026-08-16) is now satisfied:
referral accrual exists as a concrete, implemented mechanism, so
REFUNDED state machine work is UNBLOCKED and can now proceed with a
real ReferralAccrual reversal design (clawback vs. keep on refund) as
a first-class part of that work, rather than a hypothetical constraint.

Status: DEFERRED (decided 2026-08-08), referral-program precondition
RESOLVED (2026-08-17) - REFUNDED implementation itself remains not yet
started.
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
  Verified by
  tests/test_payment_critical_paths.py::test_delivery_exception_does_not_roll_back_payment_state.


---

Shared test and dev database (FIXED 2026-08-15)

Where
Before the fix: DATABASE_URL and the database used for manual dev/
bot testing pointed at the same Postgres database
(cryptobot_test_db). tests/conftest.py's autouse clean_db fixture
runs TRUNCATE TABLE ... CASCADE on every test run.

Symptom
Running pytest silently wiped manually-created dev data (a
hand-created test Product and Invoice used for live BTCPay testing
were lost mid-session after an unrelated test run).

Fix
Created a separate cryptobot_dev_db for runtime/bot use. Added
TEST_DATABASE_URL to settings.py, pointing at the original
cryptobot_test_db. DATABASE_URL now points at cryptobot_dev_db.
tests/conftest.py's reset_engine_per_test fixture now forces
get_engine()/get_sessionmaker() to bind to TEST_DATABASE_URL for the
duration of each test, and refuses to run at all
(_require_test_database_url()) if TEST_DATABASE_URL is unset or
doesn't contain "test" in the URL - a defensive guard in case the
two get swapped again in the future.
Verified: full test suite passes against cryptobot_dev_db in
isolation; deliberately unsetting TEST_DATABASE_URL causes all tests
to fail loudly instead of running against the wrong database.

---

paytest.py appears stale / inconsistent with the current pipeline

Where
app/handlers/paytest.py

Symptom
Creates a PaymentEvent directly with event_type="webhook_received"
and provider="mock", without going through process_payment_event()
at all - no idempotency_key is computed or set, and nothing consumes
the created event afterward. Does not match the shape used anywhere
else in the payment pipeline (idempotency.md: provider +
external_payment_id + event_type -> idempotency_key).

Status: RESOLVED (2026-08-19)
Removed. app/handlers/paytest.py deleted, along with its router
import/registration and menu entry in main.py. Superseded by manual
testing via the actual provider + webhook flow (as already done for
BTCPay, and as used for the referral program / refund manual UI test
on 2026-08-19) - the second of the two options this entry originally
proposed. The command also created a PaymentEvent with no
idempotency_key set (idempotency_key is nullable=False, unique=True
on the model) and was never consumed by process_payment_event, so it
could not have advanced an invoice's state under any circumstance -
confirmed dead, not merely stale, at removal time.

BootstrapCatalogUseCase hardcodes brand_id=1, breaks on empty catalog

Where
app/application/catalog/use_cases/bootstrap_catalog.py

Symptom
On a freshly-migrated, empty dev database (categories/subcategories/
product_groups/brands all empty), starting the bot
(`python -m app.main`) crashes with:
    sqlalchemy.exc.IntegrityError: ForeignKeyViolationError:
    insert or update on table "products" violates foreign key
    constraint "fk_products_brand_id"
    DETAIL: Key (brand_id)=(1) is not present in table "brands".

Cause
BootstrapCatalogUseCase.execute() only checks
`if products: return` (i.e. skips seeding if ANY product already
exists) and otherwise directly inserts a Product with brand_id=1
hardcoded, without first creating the required Category ->
Subcategory -> ProductGroup -> Brand chain (catalog_hierarchy.md:
"Brand is REQUIRED for every Product (no nullable brand)", "Every
level MUST reference its immediate parent only"). It silently
assumed brand_id=1 would already exist from some earlier manual
seeding, rather than actually bootstrapping the catalog hierarchy
itself despite the class name.

Discovered 2026-08-19 while manually testing the referral program +
refund UI end-to-end in the real Telegram bot against a genuinely
empty dev database (cryptobot_dev_db) after confirming via psql that
users/invoices/referral_accruals were all empty. Not related to the
referral program or refund work itself - a pre-existing latent bug
that a previously-seeded dev DB had been masking.

Status: RESOLVED (2026-08-20)
Fixed per option (a): BootstrapCatalogUseCase now creates the full
Category -> Subcategory -> ProductGroup -> Brand chain itself (each
level flushed to get its id before creating the next, referencing
only its immediate parent per catalog_hierarchy.md), before creating
the seed Product referencing the just-created Brand.id. The
`if products: return` no-op guard is unchanged. Verified by
tests/test_bootstrap_catalog.py::test_bootstrap_catalog_creates_full_hierarchy_on_empty_db
(confirms the full chain on a genuinely empty DB) and
::test_bootstrap_catalog_is_a_noop_when_products_already_exist
(confirms no duplicate hierarchy when a product already exists).

---

Operational Notes (not spec/code discrepancies, but worth preserving
across sessions)

cloudflared Quick Tunnel + QUIC unreliable on mobile network

Where
Termux dev environment, testing BTCPay webhooks via
`cloudflared tunnel --url http://localhost:8000`.

Symptom
Tunnel URL resolves and BTCPay UI/API traffic works, but the FastAPI
webhook route becomes unreachable partway through a session (BTCPay
webhook deliveries fail with no error code; direct curl to the
tunnel URL returns HTTP 530). cloudflared logs show repeated
"Failed to dial a quic connection: timeout" against multiple edge
IPs, while cloudflared's own precheck reports QUIC (UDP) failing and
TCP/HTTP2 succeeding, suggesting protocol=http2.

Cause
cloudflared defaults to QUIC (UDP) for the tunnel connection to
Cloudflare's edge. UDP appears not to traverse reliably on the
mobile network used for this VPS/Termux setup, causing intermittent
or total tunnel failure independent of the local server's health.

Fix
Force HTTP/2 instead of the default QUIC:
    cloudflared tunnel --protocol http2 --url http://localhost:8000
Confirmed stable after switching. If tunnel testing resumes in a
future session and webhooks silently stop arriving (with the local
`/health` endpoint still responding fine), check this first before
assuming an application-level bug.
