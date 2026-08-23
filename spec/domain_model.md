# Domain Model

---

# User

Represents Telegram user.

Fields:
- id
- telegram_id
- username
- referral_code (str, unique, generated at user creation)
- referred_by_id (FK -> User.id, nullable, self-referential, set at
  most once - see referral_program.md)

---

# Product

Represents digital good.

Fields:
- id
- title
- description
- price
- currency
- telegram_file_id
- file_type
- status (DRAFT / READY / PUBLISHED / ARCHIVED)

---

# Invoice (Aggregate Root)

Fields:
- id
- user_id
- product_id
- amount
- currency
- status (PENDING / PAID / EXPIRED / FAILED / REFUNDED)
- tx_hash
- provider
- external_payment_id
- delivered
- created_at
- expires_at

---

# ReferralAccrual

Append-only ledger tracking referral commission (see
referral_program.md and refund.md).

Fields:
- id
- invoice_id (FK -> Invoice.id, unique - one accrual per invoice)
- referrer_id (FK -> User.id)
- referred_user_id (FK -> User.id)
- amount (Numeric, fiat - always Invoice.amount-derived, never
  crypto-denominated)
- currency (str - matches Invoice.currency)
- percent (Numeric - rate snapshotted at accrual time)
- status (PENDING / PAID_OUT / CLAWED_BACK)
- created_at
- paid_out_at (nullable)

---

# PaymentEvent

Immutable webhook event log.

Fields:
- id
- invoice_id
- provider
- event_type
- payload
- processed
- retry_count
- failed
- last_error
- created_at
- idempotency_key

---

# Aggregate Rules

Invoice is the single source of truth for payment state.

All payment transitions MUST go through Invoice.

---

# Product Lifecycle

DRAFT → READY → PUBLISHED → ARCHIVED

---

# Product Invariants

- price > 0
- currency required
- telegram_file_id required for delivery
- product is purchasable ONLY if status == PUBLISHED

---

# Invoice Invariants

- PAID cannot revert to PENDING
- delivered invoice must be PAID
- delivery executed at most once
- external_payment_id must be unique
- state transitions ONLY via idempotent webhook pipeline

---

# ReferralAccrual Invariants

- append-only ledger (never mutated except status transitions and
  paid_out_at)
- one ReferralAccrual per invoice_id (unique constraint, idempotent
  per payment webhook)
- amount always fiat-denominated (Invoice.amount), independent of
  paid crypto asset or provider
- CLAWED_BACK set only via RefundInvoiceUseCase, in the same
  transaction as the invoice's REFUNDED transition (refund.md)

---

# PaymentEvent Invariants

- append-only log
- raw payload persisted
- idempotency_key unique per provider event
- fully auditable system trace

---

# Delivery Rule

Delivery MUST NOT be attempted if telegram_file_id is NULL.

This is a validation failure, not a system error.
