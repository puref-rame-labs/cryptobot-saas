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

---

# Open Question: User-Facing Provider Selection (Deferred)

Currently the buyer never chooses a provider - CreateInvoiceUseCase
resolves a single provider via settings.DEFAULT_PAYMENT_PROVIDER, and
that's the only one used for every invoice.

Letting the buyer choose (e.g. "Pay with CryptoBot" vs "Pay with
BTCPay (BTC)") is architecturally cheap to add later - the provider
abstraction (this file) already treats provider as an interchangeable
parameter, not a hardcoded dependency. It would mean: a provider-choice
keyboard in the /buy flow, and CreateInvoiceUseCase accepting
provider_name as an argument instead of reading it from settings.

Deliberately NOT done now (2026-08-22): CryptoBot is currently
disabled from the routing entirely (DEFAULT_PAYMENT_PROVIDER=btcpay,
no CRYPTOBOT_MAINNET_TOKEN provisioned on this fork). A provider-choice
UI only makes sense once at least two providers are simultaneously
live in mainnet - building it now would mean testing a selection
screen with only one real option, and re-testing it later once
CryptoBot mainnet is actually provisioned.

Revisit once CryptoBot mainnet is provisioned and verified independently
(new mainnet API token via @CryptoBot's Crypto Pay, confirmed against
live getCurrencies/getExchangeRates per testnet_mainnet_migration.md's
Open Questions - not assumed from the prior pre-fork SQLite-era test).
