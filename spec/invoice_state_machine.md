# Invoice State Machine

# States

* PENDING
* PAID
* EXPIRED
* FAILED
* REFUNDED

---

# Allowed Transitions

PENDING -> PAID

PENDING -> EXPIRED

PENDING -> FAILED

PAID -> REFUNDED

---

# Forbidden Transitions

PAID -> PENDING

EXPIRED -> PAID

FAILED -> PAID

REFUNDED -> PAID

---

# Delivery Rules

Delivery is allowed ONLY when:

* invoice.status == PAID
* invoice.delivered == False

After successful delivery:

* invoice.delivered = True

---

# Idempotency Rules

Repeated PAID events MUST NOT:

* duplicate delivery
* duplicate tx_hash mutation
* duplicate invoice transition

---

# Expiration Rules

Expired invoices cannot become payable again.

---

# Provider Rules

Provider webhook normalization MUST happen before state transition.
