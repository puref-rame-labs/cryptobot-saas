# Project Structure

# Layers

## app/domain

Pure business rules.

MUST NOT import:

* FastAPI
* aiogram
* SQLAlchemy

---

## app/services

Application use cases.

Contains:

* invoice service
* payment orchestration
* delivery orchestration

---

## app/infrastructure

External systems.

Contains:

* database
* repositories
* ORM models

---

## app/api

HTTP layer.

Contains:

* FastAPI app
* routes
* webhook endpoints

---

## app/handlers

Telegram handlers.

Contains:

* aiogram routers
* commands
* callbacks

---

# Payment Architecture

```text
providers/
    base.py
    registry.py
    mock/
```

---

# DTO Rules

DTOs located in:

```text
app/services/payments/core/dto/
```

DTOs are canonical normalized transport objects.

---

# Factory Rules

Provider instantiation only through:

```python
get_payment_provider(provider_name)
```

---

# Database Rules

Repositories MUST operate through UnitOfWork.

Direct session mutations outside UoW are forbidden.

---

# Future Planned Structure

```text
workers/
events/
delivery/
admin/
```

---

# Delivery Layer

Delivery subsystem is responsible for:

* digital content delivery
* exactly-once delivery semantics
* retry-safe execution
* delivery isolation from payment providers

---

# Delivery Rules

Delivery layer MUST NOT:

* mutate invoice payment state
* validate provider payloads
* perform payment transitions

Delivery layer ONLY:

* execute product delivery
* mark invoice as delivered
* raise delivery failures

---

# Delivery Retry Model

Delivery retries are allowed only for:

* transient Telegram failures
* network failures
* temporary infrastructure errors

Retries MUST remain idempotent.

---

# Delivery Ownership

Delivery orchestration belongs to:

```text
app/services/delivery/
```

Webhook handlers and providers MUST NOT execute delivery directly.

---

# Future Delivery Evolution

Planned future improvements:

* retry queues
* delayed retries
* dead letter queue
* distributed workers
* delivery event bus

```
```
