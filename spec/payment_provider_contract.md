# Payment Provider Contract

# Purpose

Payment providers abstract external payment systems.

Each provider MUST implement identical interface.

---

# Required Methods

## create_invoice

Signature:

```python
async def create_invoice(invoice)
```

Responsibilities:

* create external payment object
* return normalized DTO

---

## verify_signature

Signature:

```python
async def verify_signature(headers, payload)
```

Responsibilities:

* validate webhook authenticity
* return boolean

---

## normalize

Signature:

```python
async def normalize(payload)
```

Responsibilities:

* convert provider payload into canonical DTO

---

# Required DTO

normalize() MUST return:

```python
PaymentEventDTO
```

---

# PaymentEventDTO Contract

Required fields:

```python
invoice_id: int
provider: str
external_payment_id: str
status: str
```

Optional fields:

```python
tx_hash: Optional[str]
```

---

# Provider Registry

All providers MUST be registered in:

```python
app/services/payments/providers/registry.py
```

---

# Factory Rules

Provider creation MUST happen only through:

```python
get_payment_provider(provider_name)
```

---

# Provider Isolation

Providers MUST NOT:

* mutate database directly
* access Telegram bot
* execute delivery logic

Providers ONLY:

* normalize
* validate
* create external invoices
* throw exceptions for missing product state is NOT allowed in provider layer
