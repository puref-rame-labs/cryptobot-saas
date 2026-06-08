# Event Flow

## Invoice Creation Flow

User
-> Telegram Bot
-> InvoiceService
-> Invoice persisted
-> Payment provider invoice created
-> external_payment_id assigned
-> invoice committed

---

## Payment Flow

Provider
-> FastAPI webhook
-> verify_signature()
-> normalize()
-> compute idempotency_key
-> check PaymentEvent (deduplication gate)
-> persist PaymentEvent
-> if not processed:
    -> transition invoice state
    -> execute delivery
    -> mark PaymentEvent as processed

---

## Delivery Flow

Invoice PAID
-> delivery service
-> send digital content
-> invoice.delivered = True

---

## Failure Flow

Invalid signature
-> reject webhook

Invoice not found
-> persist PaymentEvent (failed)
-> return invoice_not_found

Delivery failure
-> invoice remains PAID
-> retry later (future worker system)

---

## Event Pipeline (future foundation)

webhook_received
    ->
normalized_event
    ->
idempotency_check
    ->
payment_confirmed
    ->
delivery_requested
    ->
delivery_completed
