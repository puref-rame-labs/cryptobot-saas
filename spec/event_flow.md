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

##  Payment Flow

Provider
-> FastAPI webhook
-> verify_signature()
-> normalize()
-> ingestion layer
-> persist PaymentEvent
-> process_payment_event()
-> transition invoice state
-> trigger delivery
-> mark event processed

---

# Processing Semantics

Webhook ingestion MUST remain side-effect minimal.

Responsibilities of ingestion layer:

* verify signature
* normalize provider payload
* pass canonical DTO to processing layer

Business logic MUST NOT execute directly inside HTTP route layer.

---

# Processing Layer Responsibilities

process_payment_event() is responsible for:

* idempotency guard
* invoice lookup
* state transition
* tx_hash persistence
* delivery triggering
* processed flag update

---

# Delivery Trigger Rules

Delivery execution is allowed only after:

* invoice.status == PAID
* invoice.delivered == False

---

# Failure Semantics

If delivery fails:

* invoice remains PAID
* PaymentEvent remains unprocessed
* retry becomes possible later
* delivery failure is treated as DOMAIN failure, not system failure
---

# Success Semantics

After successful processing:

* PaymentEvent.processed = True
* invoice.delivered = True

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

---

# Webhook Safety Boundary

Webhook ingestion layer MUST NEVER produce HTTP 500 for domain-level errors.

Allowed behavior:

* return controlled HTTP response (200/400/409 depending on case)
* persist PaymentEvent before processing
* isolate DeliveryService exceptions from API layer

Disallowed:

* raising unhandled exceptions from delivery or payment processing
* leaking domain errors to HTTP layer
