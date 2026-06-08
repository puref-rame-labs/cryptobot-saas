# Domain Model

# Entities

---

# User

Represents Telegram user.

Fields:

* id
* telegram_id
* username

---

# Product

Represents purchasable digital item.

Fields:

* id
* title
* description
* price
* currency
* content

---

# Invoice

Main payment aggregate root.

Fields:

* id
* user_id
* product_id
* amount
* currency
* status
* tx_hash
* provider
* external_payment_id
* delivered
* created_at
* expires_at

---

# PaymentEvent

Immutable payment event log.

Fields:

* id
* invoice_id
* provider
* event_type
* payload
* processed
* retry_count
* failed
* last_error
* created_at
* idempotency_key

---

# Aggregate Rules

Invoice is the payment aggregate root.

All payment state transitions must happen through Invoice.

---

# Invoice Invariants

* invoice cannot transition from PAID to PENDING
* delivered invoice must be PAID
* external_payment_id must be unique
* tx_hash may be null before payment
* invoice delivery must happen at most once
* state transitions MUST be triggered only via idempotent webhook pipeline

---

# PaymentEvent Invariants

* payment events are append-only
* raw provider payload must be persisted
* events must remain auditable
* idempotency_key must be unique per provider event

---

# Product Invariants

* product price must be positive
* product currency must exist
* product content cannot be empty

---

# User Invariants

* telegram_id must be unique
