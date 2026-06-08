# System Overview

## Project

Crypto payment Telegram bot for digital goods delivery.

The system allows users to:

* browse products
* create invoices
* pay with cryptocurrency
* receive digital goods automatically

---

# Core Components

## Telegram Bot

Responsible for:

* user interaction
* command handling
* invoice creation
* delivery messaging

Stack:

* aiogram

---

## API Layer

Responsible for:

* webhook receiving
* provider callbacks
* payment event ingestion

Stack:

* FastAPI
* uvicorn

---

## Payment Providers

Abstract payment gateway layer.

Current provider:

* mock

Future providers:

* Cryptomus
* NowPayments
* custom blockchain watcher

---

## Database

Stores:

* users
* products
* invoices
* payment events

Current engine:

* SQLite

Future:

* PostgreSQL

---

# Main Flow

1. User sends /buy
2. Invoice created
3. Provider invoice generated
4. User pays
5. Provider sends webhook
6. Webhook normalized
7. Invoice marked as PAID
8. Delivery executed
9. Payment event persisted

---

# Architectural Style

Hybrid layered + event-driven architecture.

Main layers:

* domain
* services
* infrastructure
* api
* handlers

---

# System Guarantees

The system must guarantee:

* invoice consistency
* idempotent webhook processing
* deterministic delivery
* provider abstraction
* atomic payment transitions

---

# Non Goals

Current MVP does NOT include:

* refunds
* subscriptions
* admin dashboard
* distributed workers
* blockchain node integration
