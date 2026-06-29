# Event Flow

---

## Invoice Creation Flow

User
→ Telegram handler
→ CreateInvoiceUseCase
→ Invoice persisted (PENDING)
→ Provider invoice created
→ external_payment_id assigned

---

## Webhook Flow

Provider
→ FastAPI webhook
→ verify_signature()
→ normalize()
→ persist PaymentEvent
→ idempotency check
→ process_payment_event()
→ invoice transition (PENDING → PAID)
→ delivery trigger
→ mark processed

---

## Processing Responsibilities

process_payment_event MUST:

- enforce idempotency gate
- load invoice
- transition state
- set tx_hash
- trigger delivery
- mark event processed

---

## Delivery Rules

Delivery runs only if:

- invoice.status == PAID
- invoice.delivered == False

---

## Failure Semantics

- webhook failure → safe response (no 500)
- delivery failure → invoice remains PAID
- retry allowed for delivery only

---

## Event Pipeline (future)

webhook_received
→ normalized_event
→ idempotency_check
→ payment_confirmed
→ delivery_requested
→ delivery_completed
