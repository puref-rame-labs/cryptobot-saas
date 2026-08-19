# Refund Handling

---

# Purpose

Allow an admin to manually mark a PAID invoice as REFUNDED, closing
the architectural gap tracked in known_issues.md item 2 ("REFUNDED
state is entirely absent from the state machine"). No provider
integration — CryptoBot and BTCPay currently specify no refund
webhook, so provider-triggered refunds are explicitly out of scope
(see Open Questions / Non-Goals below).

---

# Scope

Applies to:
- Invoice state machine (app/domain/invoice/state_machine.py)
- New RefundInvoiceUseCase
- New /refund admin handler
- ReferralAccrual clawback (same transaction as the refund)

Does NOT apply to:
- Payment provider contract (unchanged — providers remain unaware
  of refunds, same principle as referral_program.md's stance on
  providers being unaware of referrals)
- Automatic/webhook-triggered refunds (deferred — see Non-Goals)
- Partial refunds (all-or-nothing per invoice in v1)

---

# State Machine Change

New allowed transitions:

    PAID -> REFUNDED
    DELIVERED -> REFUNDED

invoice_state_machine.md's "Allowed Transitions" section only listed
PAID -> REFUNDED explicitly. DELIVERED -> REFUNDED is added here as a
practical necessity, not a spec deviation: in process_payment_event.py,
PAID and DELIVERED happen within the same webhook transaction,
milliseconds apart (checkpoint commit, then immediate delivery). By the
time an admin becomes aware of a refund request (a user reports a bad
file, a dispute, etc. — realistically hours or days later), the invoice
is almost always already DELIVERED, not PAID. Restricting refund to
PAID only would make /refund unusable for the actual common case.

No new Invoice.status storage change needed — status is already a
free-form String(32) column (see domain_model.md / models.py), so
adding "REFUNDED" as a valid value requires no migration by itself.

Forbidden transitions remain forbidden — REFUNDED is terminal, same
as DELIVERED. No REFUNDED -> anything transition exists.

---

# Trigger: Manual Admin Action Only (v1)

RESOLVED (this spec): the only trigger is an admin-invoked command,
mirroring the existing publish.py / archive.py / referral_payouts.py
pattern (inline `if message.from_user.id not in settings.ADMIN_IDS`
check, no separate IsAdminFilter).

    /refund <invoice_id>

Preconditions checked before transition:
- invoice.status in {PAID, DELIVERED} (any other status -> reject
  with a clear message, mirroring publish.py's "Нельзя опубликовать
  из статуса X")
- invoice exists

No refund reason/amount field in v1 — this is a binary state flip,
not a partial-refund ledger. If reason tracking becomes a real need,
revisit as a follow-up (see Non-Goals).

---

# ReferralAccrual Clawback (Idempotency Integration)

known_issues.md item 2's note (2026-08-16) identified the abuse
vector this section closes: without REFUNDED being aware of referral
accrual, a self-referral or colluding accounts could purchase to
trigger a referral payout, then refund the purchase while keeping
the accrued bonus.

RefundInvoiceUseCase, in the SAME transaction/checkpoint as the
PAID -> REFUNDED transition:

1. Load invoice, verify status == PAID
2. Transition invoice.status -> REFUNDED
3. IF a ReferralAccrual exists for this invoice_id AND its status
   is still PENDING:
     set ReferralAccrual.status = "CLAWED_BACK"
4. IF the ReferralAccrual status is already PAID_OUT:
     leave it untouched, but surface this to the admin in the
     command's response (e.g. "Внимание: комиссия уже выплачена
     рефереру и не может быть отозвана автоматически") — this is a
     known v1 limitation, not silently ignored. Manual reconciliation
     between admin and referrer is expected in this case, consistent
     with the overall manual-payout philosophy of referral_program.md.

New ReferralAccrualStatus value: CLAWED_BACK (alongside existing
PENDING / PAID_OUT). Appended, not replacing existing values —
append-only ledger philosophy preserved (referral_program.md).

This clawback logic lives inside RefundInvoiceUseCase, not as a
separate best-effort step — same principle as referral_program.md's
accrual trigger ("not a separate, independently triggered process").

---

# Non-Goals (v1)

- Provider refund webhooks (CryptoBot Transfer API reversal, BTCPay
  refund flow) — no provider currently specifies this contract.
  Revisit if/when a provider adds one, per known_issues.md item 2's
  original deferral rationale.
- Partial refunds
- Refund reason/audit-note field
- Automatic re-clawback if a PAID_OUT accrual's referrer later
  returns the commission manually (purely an operational/manual
  reconciliation matter outside the bot in v1)
- User-facing refund request flow (admin-initiated only, no /buy-side
  self-service refund command)

---

# Invariants

- PAID -> REFUNDED and DELIVERED -> REFUNDED are the only new
  transitions; REFUNDED is terminal
- Refund trigger is manual admin action only, no provider awareness
  (mirrors payment_provider_contract.md's "Providers ONLY transform
  data / validate signatures / interact with external API")
- ReferralAccrual clawback happens in the SAME transaction as the
  REFUNDED transition — never a separate best-effort pass
- A PENDING accrual on a refunded invoice MUST be marked CLAWED_BACK,
  never silently left as PENDING (would allow eventual payout of a
  clawed-back commission)
- A PAID_OUT accrual on a refunded invoice is left untouched but
  flagged to the admin — no automatic monetary reversal in v1

---

# Migration

No schema migration strictly required (status remains a free-form
String(32) column). If the team later wants a DB-level CHECK
constraint enumerating valid status values, that would be a separate,
optional follow-up — not required for this spec.
