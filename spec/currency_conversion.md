# Currency Conversion

---

# Purpose

Product prices are denominated in fiat (RUB), matching how goods are
sourced (resale from ruble-based marketplaces). Payment providers are
responsible for converting the fiat amount into the cryptocurrency
the buyer actually pays with, at the moment of invoice creation.

---

# Pricing Model

Product.price / Product.currency — always fiat (RUB).

No direct crypto-denominated products are supported. This is a
deliberate simplification: the business model is resale, sourced in
RUB, so a parallel crypto-pricing path is not needed.

---

# Provider Contract Change

create_invoice(invoice) now always operates on a fiat amount:

- invoice.amount   — fiat amount (RUB)
- invoice.currency — fiat currency code (RUB)

Providers MUST convert fiat -> crypto themselves and return the
resulting payment object (payment_url, external_id, and — once
available, e.g. after webhook — paid_asset / paid_amount /
paid_fiat_rate).

This is the ONLY invoice creation path. There is no separate
crypto-denominated invoice path.

---

# CryptoBot Provider

Uses createInvoice with:
- currency_type = "fiat"
- fiat = invoice.currency (RUB)
- amount = invoice.amount

CryptoBot performs the fiat -> crypto conversion at the moment the
buyer pays (rate is live until payment, not frozen at invoice
creation). After payment, the webhook payload includes paid_asset,
paid_amount, and paid_fiat_rate — these are persisted on Invoice.

---

# Mock Provider

Emulates fiat -> crypto conversion using a hardcoded test rate
(no external calls). Exists solely to keep the provider interface
uniform for local/dev testing — does not need to reflect real rates.

---

# Invoice Fields (new)

- paid_asset (str, nullable)     — crypto asset actually paid with (e.g. "BTC", "USDT")
- paid_amount (Numeric, nullable) — amount paid in paid_asset
- paid_fiat_rate (Numeric, nullable) — rate of paid_asset valued in invoice.currency at payment time

These fields are populated only after a successful payment webhook.
They exist for audit/bookkeeping — reconciling what was actually
received against what was priced.

---

# Migration Note

Existing test products (priced in USDT) will be deleted and
recreated with RUB pricing once this spec is implemented. No
historical price migration is needed — these are dev/test records.

---

# Open Questions (deferred)

- Whether to support providers without fiat conversion capability —
  deferred until such a provider is actually needed.
