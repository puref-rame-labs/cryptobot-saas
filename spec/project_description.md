# Project Description

# Project Name

cryptobot

---

# Purpose

Telegram bot for selling digital goods through cryptocurrency payments with automatic delivery.

The system is designed as a modular payment-processing platform with provider abstraction and event-driven architecture foundations.

---

# Current Development Stage

MVP / early production architecture.

Core payment lifecycle is operational.

Main focus:

* architectural stabilization
* provider abstraction
* idempotent webhook processing
* delivery consistency
* event-driven evolution

---

# Main User Flow

1. User opens Telegram bot
2. User executes /buy
3. System creates invoice
4. Payment provider generates external payment
5. User pays invoice
6. Provider sends webhook
7. System validates webhook
8. Invoice becomes PAID
9. Digital product delivered automatically

---

# Main Technologies

## Backend

* Python 3.13
* asyncio

## Telegram

* aiogram

## API

* FastAPI
* uvicorn

## Database

* SQLAlchemy
* SQLite

## Runtime Environment

Current development environment:

* Termux
* Android host

---

# Architectural Principles

## Provider Abstraction

Payment providers must be interchangeable through unified interfaces.

---

## Event-Driven Orientation

Webhook events are normalized into canonical internal events.

---

## Idempotency

Repeated payment events must not duplicate delivery or corrupt state.

---

## Explicit State Machine

Invoice lifecycle is controlled through deterministic state transitions.

---

## Layer Separation

Project follows layered architecture:

* domain
* services
* infrastructure
* api
* handlers

---

# Current Implemented Features

Implemented:

* Telegram /buy flow
* invoice creation
* provider abstraction
* mock payment provider
* webhook ingestion
* webhook normalization
* payment event persistence
* invoice payment transition
* digital delivery
* idempotent delivery protection

---

# Current Known Limitations

Not yet implemented:

* distributed workers
* retries queue
* PostgreSQL
* admin panel
* real crypto providers
* refund support
* observability stack
* transactional outbox

---

# Long-Term Direction

Planned evolution:

* production-grade payment architecture
* real blockchain providers
* asynchronous workers
* event bus
* delivery retry subsystem
* PostgreSQL migration
* scalable deployment topology

---

# Development Methodology

Project uses Spec-Driven Development (SDD).

Architecture and invariants are defined in spec/ before major implementation changes.

The specification is considered the primary source of architectural truth.
