# Idempotency Model

---

## Scope

Applies ONLY to external webhooks.

---

## Idempotency Key

provider + external_payment_id + event_type

If event_type missing → "payment"

idempotency_key = hash(combined string)

---

## Core Rule

Before any side effects:

1. compute key
2. check PaymentEvent
3. if processed == True → NO-OP
4. else continue

---

## Enforcement Layer

MUST be in application layer:

- use-case
- payment processing service

NOT in:

- handler
- provider
- API route

---

## Side Effects Allowed Once

- invoice transition
- tx_hash assignment
- delivery trigger

---

## Delivery Rule

Delivery MUST execute at most once.

Controlled by:

invoice.delivered

---

## Duplicate Events

- always stored
- processed only once
- safe replays guaranteed

---

## Failure Mode

- failed events stored
- retry allowed
- no state corruption
