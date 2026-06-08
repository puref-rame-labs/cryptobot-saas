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
