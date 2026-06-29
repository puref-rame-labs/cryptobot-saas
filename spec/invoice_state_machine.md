# Invoice State Machine

---

# States

- PENDING
- PAID
- EXPIRED
- FAILED
- REFUNDED

---

# Allowed Transitions

PENDING → PAID  
PENDING → EXPIRED  
PENDING → FAILED  
PAID → REFUNDED  

---

# Forbidden Transitions

PAID → PENDING  
EXPIRED → PAID  
FAILED → PAID  
REFUNDED → PAID  

---

# Delivery Rule

Delivery allowed ONLY when:

- status == PAID
- delivered == False

After success:

- delivered = True

Delivery failure does NOT change invoice state.

---

# Idempotency Constraint

Repeated PAID events MUST NOT:

- re-trigger delivery
- mutate tx_hash again
- re-apply state transitions
