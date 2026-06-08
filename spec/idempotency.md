# idempotency
```md
# Idempotency Rules

# Purpose

Webhook retries are expected behavior.

The system MUST remain deterministic under repeated external events.

---

# Scope

This specification applies to:

- payment webhooks
- provider callbacks
- all external payment event ingestion

It does NOT apply to internal domain events.

---

# Canonical Idempotency Key

Each external event is identified by:

```

provider + external_payment_id + event_type

```

If `event_type` is missing, default value MUST be:

```

payment

```

Canonical form:

```

idempotency_key = hash(provider + external_payment_id + event_type)

```

---

# Core Principle

The system guarantees:

- at-least-once event ingestion
- exactly-once business effect execution

---

# Idempotency Gate (REQUIRED)

Before any business logic execution:

1. Compute `idempotency_key`
2. Search PaymentEvent by `idempotency_key`
3. If exists AND processed == True:
   - STOP execution (NO-OP)
4. Else:
   - continue pipeline

This gate MUST be enforced in application service layer.

---

# Processing Rules

All webhook events MUST:

- be persisted as PaymentEvent
- be traceable for audit purposes

Even duplicate or failed events.

---

# Side Effect Constraints

Only one execution is allowed for:

- invoice state transition (PENDING → PAID)
- delivery execution
- tx_hash assignment

Repeated events MUST NOT trigger these again.

---

# Delivery Protection Rule

Delivery MUST execute at most once.

Controlled by:

```

invoice.delivered

```

Delivery is allowed ONLY when:

- invoice.status == PAID
- invoice.delivered == False

---

# Duplicate Event Behavior

If the same webhook is received multiple times:

Expected behavior:

- PaymentEvent is stored every time
- invoice state changes only once
- delivery executes only once
- subsequent events become NO-OP

---

# Failure Handling

If processing fails after persistence:

- PaymentEvent.retry_count increases
- processed remains False
- system may retry later (future worker system)

---

# Consistency Model

System provides:

- at-least-once ingestion
- exactly-once state transition
- exactly-once delivery side effects

---

# Enforcement Location

Idempotency MUST NOT be implemented in:

- provider layer
- Telegram handlers
- API routing layer

It MUST be implemented in:

- application service / webhook use case layer

---

# Future Extensions

Possible improvements:

- deduplication via database unique constraint on idempotency_key
- distributed locks (if scaling requires)
- transactional outbox pattern
- event-driven processing pipeline
```
