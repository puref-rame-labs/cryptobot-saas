from decimal import Decimal
from types import SimpleNamespace

from sqlalchemy import select

from app.application.payments.use_cases.process_payment_event import process_payment_event
from app.application.invoice.use_cases.refund_invoice import RefundInvoiceUseCase
from app.infrastructure.database.session import get_sessionmaker
from app.infrastructure.database.models import Invoice, ReferralAccrual
from app.infrastructure.database.uow import UnitOfWork


def make_normalized(external_payment_id: str):
    return SimpleNamespace(
        external_payment_id=external_payment_id,
        tx_hash="tx_refund_test",
        paid_asset="BTC",
        paid_amount=Decimal("0.001"),
        paid_fiat_rate=Decimal("8000000.00"),
    )


async def test_refund_delivered_invoice_with_pending_accrual_claws_back(
    seeded_invoice_with_referrer_no_payment, mock_bot
):
    """
    refund.md: DELIVERED -> REFUNDED is the realistic common case (the
    invoice is DELIVERED within the same webhook transaction, well
    before an admin ever sees a refund request). The PENDING
    ReferralAccrual for this invoice must be clawed back in the SAME
    transaction as the REFUNDED transition.
    """
    fixture = seeded_invoice_with_referrer_no_payment
    invoice_id = fixture["invoice_id"]

    normalized = make_normalized(fixture["external_payment_id"])
    result = await process_payment_event(normalized, "cryptobot")
    assert result["status"] == "accepted"

    sessionmaker = get_sessionmaker()
    session = sessionmaker()
    try:
        invoice = await session.get(Invoice, invoice_id)
        assert invoice.status == "DELIVERED", (
            "Precondition for this test: invoice must reach DELIVERED "
            f"via the real pipeline, got '{invoice.status}'"
        )

        accrual = (await session.execute(
            select(ReferralAccrual).where(
                ReferralAccrual.invoice_id == invoice_id
            )
        )).scalar_one()
        assert accrual.status == "PENDING", (
            "Precondition: accrual must start PENDING before refund"
        )
    finally:
        await session.close()

    async with UnitOfWork() as uow:
        invoice = await uow.invoices.get_by_id(invoice_id)

        refund_uc = RefundInvoiceUseCase(uow)
        refund_result = await refund_uc.execute(invoice)

        assert refund_result["ok"] is True, (
            f"refund.md: DELIVERED -> REFUNDED must be allowed, "
            f"got: {refund_result}"
        )
        assert refund_result["clawback_warning"] is None

        await uow.session.commit()

    session = sessionmaker()
    try:
        fresh_invoice = await session.get(Invoice, invoice_id)
        assert fresh_invoice.status == "REFUNDED", (
            "invoice.status must be REFUNDED after a successful refund, "
            f"got '{fresh_invoice.status}'"
        )

        fresh_accrual = (await session.execute(
            select(ReferralAccrual).where(
                ReferralAccrual.invoice_id == invoice_id
            )
        )).scalar_one()
        assert fresh_accrual.status == "CLAWED_BACK", (
            "refund.md: 'A PENDING accrual on a refunded invoice MUST "
            "be marked CLAWED_BACK, never silently left as PENDING.' "
            f"Got status '{fresh_accrual.status}'"
        )
    finally:
        await session.close()


async def test_refund_with_already_paid_out_accrual_leaves_it_untouched_and_warns(
    seeded_invoice_with_referrer_no_payment, mock_bot
):
    """
    refund.md: 'IF the ReferralAccrual status is already PAID_OUT: leave
    it untouched, but surface this to the admin' - known v1 limitation,
    not silently ignored.
    """
    fixture = seeded_invoice_with_referrer_no_payment
    invoice_id = fixture["invoice_id"]

    normalized = make_normalized(fixture["external_payment_id"])
    result = await process_payment_event(normalized, "cryptobot")
    assert result["status"] == "accepted"

    # Simulate the admin having already paid out the referrer via
    # /referral_payouts before the refund request comes in.
    async with UnitOfWork() as uow:
        accrual = await uow.referral_accruals.get_by_invoice_id(invoice_id)
        accrual.status = "PAID_OUT"
        await uow.session.commit()

    async with UnitOfWork() as uow:
        invoice = await uow.invoices.get_by_id(invoice_id)

        refund_uc = RefundInvoiceUseCase(uow)
        refund_result = await refund_uc.execute(invoice)

        assert refund_result["ok"] is True
        assert refund_result["clawback_warning"] is not None, (
            "refund.md: an already-PAID_OUT accrual must produce an "
            "admin-facing warning, not be silently ignored"
        )

        await uow.session.commit()

    sessionmaker = get_sessionmaker()
    session = sessionmaker()
    try:
        fresh_invoice = await session.get(Invoice, invoice_id)
        assert fresh_invoice.status == "REFUNDED"

        fresh_accrual = (await session.execute(
            select(ReferralAccrual).where(
                ReferralAccrual.invoice_id == invoice_id
            )
        )).scalar_one()
        assert fresh_accrual.status == "PAID_OUT", (
            "refund.md: a PAID_OUT accrual must be left untouched - no "
            f"automatic monetary reversal in v1. Got '{fresh_accrual.status}'"
        )
    finally:
        await session.close()


async def test_refund_rejects_invoice_not_in_paid_or_delivered(seeded_invoice):
    """
    refund.md preconditions: invoice.status must be in {PAID, DELIVERED}.
    seeded_invoice starts as PENDING - refund must be rejected.
    """
    async with UnitOfWork() as uow:
        invoice = await uow.invoices.get_by_id(seeded_invoice)
        assert invoice.status == "PENDING"

        refund_uc = RefundInvoiceUseCase(uow)
        refund_result = await refund_uc.execute(invoice)

        assert refund_result["ok"] is False
        assert refund_result["reason"] == "invalid_status"
        assert invoice.status == "PENDING", "Status must not change on rejection"

        await uow.session.rollback()


async def test_refunded_invoice_cannot_be_refunded_again(
    seeded_invoice_with_referrer_no_payment, mock_bot
):
    """
    refund.md: REFUNDED is terminal - no REFUNDED -> anything transition.
    """
    fixture = seeded_invoice_with_referrer_no_payment
    invoice_id = fixture["invoice_id"]

    normalized = make_normalized(fixture["external_payment_id"])
    await process_payment_event(normalized, "cryptobot")

    async with UnitOfWork() as uow:
        invoice = await uow.invoices.get_by_id(invoice_id)
        refund_uc = RefundInvoiceUseCase(uow)
        first = await refund_uc.execute(invoice)
        assert first["ok"] is True
        await uow.session.commit()

    async with UnitOfWork() as uow:
        invoice = await uow.invoices.get_by_id(invoice_id)
        assert invoice.status == "REFUNDED"

        refund_uc = RefundInvoiceUseCase(uow)
        second = await refund_uc.execute(invoice)

        assert second["ok"] is False, (
            "REFUNDED is terminal - a second refund attempt must be rejected"
        )
        assert invoice.status == "REFUNDED"

        await uow.session.rollback()
