# System Overview

## Project

cryptobot — Telegram bot for selling digital goods via cryptocurrency payments with automated delivery.

---

## Core Architecture

Hybrid layered + event-driven system:

- domain (pure rules)
- services (use-cases)
- infrastructure (DB, providers)
- api (webhooks)
- handlers (Telegram UI)

---

## Main Flow

1. User sends /buy
2. System checks PRODUCT is PUBLISHED
3. Invoice is created (PENDING)
4. Payment provider creates external invoice
5. User pays externally
6. Provider sends webhook
7. Webhook is normalized + deduplicated
8. Invoice becomes PAID
9. Delivery is executed
10. PaymentEvent stored

---

## System Guarantees

- Exactly-once invoice state transition
- Exactly-once delivery
- At-least-once webhook ingestion
- Provider abstraction
- Deterministic state machine behavior

---

## Product Gate Rule (CRITICAL)

Only PUBLISHED products are purchasable.

READY is NOT purchasable.

---

## Current Stack

- Python 3.13
- aiogram
- FastAPI
- SQLAlchemy
- SQLite (dev)

---

## Non-goals (MVP)

- refunds
- distributed workers
- blockchain node integration
- admin panel
- observability stack
