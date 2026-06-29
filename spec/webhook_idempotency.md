# Webhook Idempotency

---

## Purpose

Guarantee exactly-once effects under at-least-once delivery.

---

## Algorithm

1. compute idempotency_key
2. check PaymentEvent
3. if exists AND processed → STOP
4. persist event
5. process event

---

## Guarantees

- at-least-once ingestion
- exactly-once business effect
- deterministic replay behavior

---

## Side Effect Scope

Allowed ONLY after gate:

- invoice transition
- delivery trigger

---

## Persistence Rule

EVERY webhook event must be stored.

Even invalid ones.
