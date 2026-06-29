# Payment Provider Contract

---

## Purpose

Unified abstraction over external payment systems.

---

## Interface

### create_invoice

async def create_invoice(invoice)

- creates external payment object
- returns PaymentDTO

---

### verify_signature

async def verify_signature(headers, payload)

- validates webhook authenticity
- returns bool

---

### normalize

async def normalize(payload)

- converts provider payload into canonical DTO

---

## DTO Contract

PaymentEventDTO:

- invoice_id
- provider
- external_payment_id
- status
- tx_hash (optional)

---

## Provider Rules

Providers MUST NOT:

- access DB
- perform delivery
- enforce product state rules
- contain business logic

Providers ONLY:

- transform data
- validate signatures
- interact with external API
