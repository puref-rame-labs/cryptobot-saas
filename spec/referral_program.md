# Referral Program

---

# Purpose

Reward a user (referrer) with a percentage of every purchase made by
a user they referred (referred_user). No CRM needed — this is an
additional use case layered onto the existing User/Invoice model,
following the same append-only ledger pattern as PaymentEvent.

---

# Scope

Applies to:
- User model (new fields)
- New ReferralAccrual entity
- Invoice payment pipeline (process_payment_event.py)
- New /start deep-link handling
- New /referral(s) handler for stats

Does NOT apply to:
- Invoice/Product state machines (unchanged)
- Payment provider contract (unchanged — providers remain unaware of referrals)
- Refund handling — REFUNDED state does not currently exist
  (known_issues.md item 2). Accrual reversal on refund is explicitly
  OUT OF SCOPE here and must be designed together with REFUNDED when
  that work happens, not retrofitted onto this spec.

---

# Domain Model Changes

## User (extended)

New fields:
- referral_code (str, unique, generated at user creation)
- referred_by_id (FK → User.id, nullable, self-referential)

Rules:
- referred_by_id is set AT MOST ONCE, on first /start with a
  referral parameter (t.me/bot?start=ref_<code>).
- referred_by_id is immutable once set — a later /start with a
  different ref code MUST NOT overwrite it.
- A user CANNOT refer themselves (referred_by_id != self.id).
- referred_by_id may be NULL (organic user, no referrer).

## ReferralAccrual (new, append-only ledger)

Fields:
- id
- invoice_id (FK → Invoice.id)
- referrer_id (FK → User.id)
- referred_user_id (FK → User.id)
- amount (Numeric — commission amount, fiat RUB)
- currency (str — matches Invoice.currency)
- percent (Numeric — rate applied, snapshotted at accrual time)
- status (PENDING / PAID_OUT)
- created_at
- paid_out_at (nullable)

Invariants:
- Append-only. Never mutated except status PENDING → PAID_OUT and
  paid_out_at.
- One ReferralAccrual per (invoice_id) — a given purchase accrues
  commission at most once, enforced same way as PaymentEvent
  idempotency (unique constraint on invoice_id).
- amount is computed from Invoice.amount (fiat), NOT from
  paid_amount/paid_asset (currency_conversion.md) — commission is
  fiat-denominated regardless of what crypto asset the buyer paid
  with, so it isn't exposed to BTCPay's rate-lock risk
  (btcpay_provider.md) or CryptoBot's live-rate variance.

---

# Commission Rule

Percentage applies to EVERY purchase made by a referred user, not
just their first. No cap, no decay — flat rate per purchase.

Rate is a single global config value (e.g. REFERRAL_PERCENT in
settings.py) at launch. Per-referrer custom rates are out of scope
for v1.

---

# Accrual Trigger (Idempotency Integration)

Accrual is a side effect of the SAME idempotent webhook pipeline
that handles invoice transition and delivery (idempotency.md,
webhook_idempotency.md) — it MUST NOT be a separate, independently
triggered process.

Updated side-effect list for process_payment_event (extends
idempotency.md's "Side Effects Allowed Once"):

- invoice transition
- tx_hash assignment
- delivery trigger
- referral accrual   <- NEW

Placement in process_payment_event.py:
1. idempotency gate (unchanged)
2. invoice transition to PAID (unchanged, checkpoint commit per
   known_issues.md fix)
3. IF invoice.user.referred_by_id IS NOT NULL:
     create ReferralAccrual (referrer_id = referred_by_id,
     referred_user_id = invoice.user_id, amount = invoice.amount *
     REFERRAL_PERCENT, status = PENDING)
4. delivery trigger (unchanged, wrapped in try/except per
   known_issues.md fix)

Accrual creation happens in the SAME transaction/checkpoint as the
PAID transition (step 2), not after delivery — delivery failure
must not affect whether commission was recorded, mirroring
"Delivery failure does NOT change invoice state"
(invoice_state_machine.md).

Repeated PAID events for the same invoice (replay) MUST NOT create a
second ReferralAccrual — enforced via the unique constraint on
invoice_id, same pattern as PaymentEvent.idempotency_key.

---

# Payout (Manual, v1)

No CryptoBot Transfer API integration in v1. Payout mechanism:

1. Admin runs a command/handler (e.g. /referral_payouts) that lists
   referrers with status=PENDING accruals, grouped by referrer,
   summed by amount.
2. Admin pays the referrer manually (outside the bot — direct
   transfer, cash, whatever the operational process is).
3. Admin marks accruals as PAID_OUT via an admin action (bulk, per
   referrer) — sets status=PAID_OUT and paid_out_at=now() on all
   affected ReferralAccrual rows.

No partial payout tracking in v1 (it's all-or-nothing per referrer
per payout action) — if partial payouts become a real need, revisit.

---

# User-Facing Flow

1. Referrer shares t.me/bot?start=ref_<their_code>
2. New user opens bot -> /start handler parses ref_<code> ->
   RegisterReferral use-case sets referred_by_id if unset and code
   is valid and not self-referral
3. Referred user makes purchases as normal — no UI difference
4. On each PAID webhook, accrual happens transparently (no user
   notification in v1 — optional future enhancement)
5. Referrer can check accumulated PENDING commission via
   /referral_stats (their own accruals only)

---

# Invariants

- referred_by_id set at most once, never overwritten
- No self-referral
- One ReferralAccrual per invoice_id (idempotent)
- Accrual amount is always fiat (Invoice.amount), independent of
  payment provider or paid crypto asset
- Accrual creation is part of the same idempotent pipeline as
  invoice PAID transition — not a separate trigger, not
  best-effort
- Referral logic contains NO payment provider awareness (providers
  remain ignorant of referrals, per payment_provider_contract.md's
  "Providers ONLY transform data / validate signatures / interact
  with external API")

---

# Explicit Non-Goals (v1)

- Refund-aware accrual reversal — deferred until REFUNDED exists
  (known_issues.md item 2). When REFUNDED is implemented, this spec
  MUST be revisited: a refunded invoice's ReferralAccrual needs a
  defined outcome (clawback vs. keep) as part of the same
  transaction as the refund, per the self-referral/collusion abuse
  vector already flagged in known_issues.md item 2's note.
- Automatic payout (CryptoBot Transfer API or otherwise)
- Per-referrer custom commission rates
- Multi-level/tiered referrals (referrer-of-a-referrer)
- Referred-user-facing notification of accrual

---

# Migration

New Alembic migration:
- users: add referral_code (unique, indexed), referred_by_id
  (FK -> users.id, nullable)
- referral_accruals: new table per fields above, unique index on
  invoice_id

render_as_batch not required (PostgreSQL, per postgres_migration.md).
