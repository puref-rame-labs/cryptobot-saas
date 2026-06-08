# Webhook Idempotency Specification

## Purpose

Ensure deterministic and exactly-once business effects under at-least-once webhook delivery.

---

## Idempotency Key Definition

Each webhook event MUST be uniquely identified by:

- provider
- external_payment_id
- event_type (optional but recommended)

Canonical idempotency key:
idempotency_key = hash(provider + external_payment_id + event_type)


If event_type is missing, use "payment" as default.

---

## Processing Rule

Before ANY side effects:

1. Compute idempotency_key
2. Check PaymentEvent with same idempotency_key
3. If exists AND processed == True → STOP (no-op)
4. Otherwise continue processing

---

## Enforcement Point

Idempotency MUST be enforced in application layer:

- app/services/payment_service.py
- or webhook use case handler

NOT in:

- provider layer
- API layer
- Telegram handlers

---

## Allowed Side Effects (after passing gate)

Only after idempotency validation:

- persist PaymentEvent
- invoice state transition
- delivery trigger

---

## Persistence Rule

All webhook events MUST be persisted regardless of processing result.

---

## Failure Mode Handling

If duplicate webhook arrives:

- PaymentEvent is still stored (audit log)
- invoice MUST NOT change state again
- delivery MUST NOT execute again

---

## System Guarantee

System guarantees:

- at-least-once ingestion
- exactly-once business effects
  (invoice transition + delivery)
