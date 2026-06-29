# Project Structure

---

## Layers

### domain

Pure business rules:

- Product lifecycle
- Invoice state machine
- invariants

NO dependencies on frameworks.

---

### services (application layer)

Use-cases:

- CreateInvoice
- AttachProductFile
- PublishProduct
- ProcessPaymentEvent
- Delivery orchestration

---

### infrastructure

External systems:

- SQLAlchemy models
- repositories
- payment providers
- UoW

---

### api

FastAPI:

- webhook endpoints
- provider ingestion

---

### handlers

Telegram interface:

- FSM flows
- command handlers

NO business rules allowed.
