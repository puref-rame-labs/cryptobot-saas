# Invoice State Machine

---

# States

- PENDING
- PAID
- EXPIRED
- FAILED
- REFUNDED

---

# Allowed Transitions

PENDING → PAID  
PENDING → EXPIRED  
PENDING → FAILED  
PAID → REFUNDED  

---

# Forbidden Transitions

PAID → PENDING  
FAILED → PAID  
REFUNDED → PAID  

# Intentional Exception: EXPIRED → PAID (late payment)

EXPIRED → PAID IS ALLOWED, by deliberate design ("late payment
accepted" pattern), NOT a bug. Implemented in
app/domain/invoice/state_machine.py and logged via
mark_paid.py ("Late payment accepted for invoice %s (was EXPIRED,
now PAID, tx_hash=%s)").

Rationale (decided 2026-08-08, confirmed 2026-08-15):
- CryptoBot (currency_conversion.md): fiat -> crypto rate is live
  until the moment of payment, so a late CryptoBot payment carries
  near-zero price risk regardless of how late it arrives.
- BTCPay (btcpay_provider.md): rate is LOCKED at invoice creation
  and held only for the expiration window. A late payment here is
  honored at the stale, locked rate - a genuine real-money exposure
  if BTC has moved between creation and actual payment/confirmation.
- This exposure was reproduced live on 2026-08-15: invoice #8 (5000
  RUB) expired while webhook delivery was delayed ~90 minutes by an
  infrastructure issue (cloudflared tunnel), and was still honored
  at the original locked rate when the webhook eventually arrived.
- Estimated typical exposure: for delays in the tens-of-minutes
  range, expected BTC/RUB movement is on the order of a few tenths
  of a percent (based on ~30-45% annualized BTC volatility,
  time-scaled) - immaterial at typical order sizes. Tail risk (sharp
  moves during news/liquidation events) is not bounded by this
  estimate and could be materially larger if a delay coincides with
  one.
- No upper bound on lateness is currently enforced - a payment
  arriving arbitrarily late (hours, days) is still honored at the
  original rate. This is accepted for now given current order sizes
  and BTCPay's low volume, but is the main residual risk of keeping
  this behavior as-is.

Decision: KEEP EXPIRED → PAID as allowed (option (a) from
known_issues.md item 1), formalized here rather than treated as a
spec/code conflict. No time-based upper bound added at this time -
revisit if order sizes grow or infrastructure-induced delivery
delays (as seen 2026-08-15) become frequent rather than exceptional.

---

# Delivery Rule

Delivery allowed ONLY when:

- status == PAID
- delivered == False

After success:

- delivered = True

Delivery failure does NOT change invoice state.

---

# Idempotency Constraint

Repeated PAID events MUST NOT:

- re-trigger delivery
- mutate tx_hash again
- re-apply state transitions
