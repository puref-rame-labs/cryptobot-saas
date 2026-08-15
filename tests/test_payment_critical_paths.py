from decimal import Decimal
from types import SimpleNamespace

from sqlalchemy import select, func

from app.application.payments.use_cases.process_payment_event import process_payment_event
from app.application.invoice.use_cases.deliver_invoice import DeliverInvoiceUseCase
from app.application.invoice.use_cases.mark_paid import MarkInvoicePaidUseCase
from app.application.delivery.service import DeliveryService
from app.infrastructure.database.session import get_sessionmaker
from app.infrastructure.database.models import Invoice, PaymentEvent
from app.infrastructure.database.uow import UnitOfWork
import app.application.bot_instance as bot_instance


def make_normalized(external_payment_id: str):
    return SimpleNamespace(
        external_payment_id=external_payment_id,
        tx_hash="tx_test",
        paid_asset="BTC",
        paid_amount=Decimal("0.001"),
        paid_fiat_rate=Decimal("8000000.00"),
    )


async def test_webhook_for_unknown_invoice_is_still_persisted(mock_bot):
    """
    webhook_idempotency.md: "EVERY webhook event must be stored. Even invalid ones."
    """
    normalized = make_normalized("ext-does-not-exist")

    result = await process_payment_event(normalized, "cryptobot")

    assert result["status"] == "invoice_not_found"

    sessionmaker = get_sessionmaker()
    session = sessionmaker()
    try:
        event_count = await session.scalar(
            select(func.count()).select_from(PaymentEvent)
        )
        assert event_count == 1, (
            "webhook_idempotency.md требует персистить КАЖДОЕ событие, "
            f"включая невалидные (invoice не найден). Найдено записей: {event_count}"
        )
    finally:
        await session.close()


async def test_delivery_failure_does_not_change_invoice_state(seeded_invoice_no_file):
    """
    invoice_state_machine.md: "Delivery failure does NOT change invoice state."
    Товар без telegram_file_id -> доставка обязана провалиться (missing_file).
    Ожидание: invoice.status остаётся PAID, а не переходит в FAILED.
    """
    async with UnitOfWork() as uow:
        invoice = await uow.invoices.get_by_id(seeded_invoice_no_file)

        mark_paid_uc = MarkInvoicePaidUseCase(uow)
        ok = await mark_paid_uc.execute(invoice, tx_hash="tx_no_file")
        assert ok is True
        assert invoice.status == "PAID"

        delivery_service = DeliveryService(uow=uow)
        deliver_uc = DeliverInvoiceUseCase(delivery_service)
        delivered = await deliver_uc.execute(invoice)

        assert delivered is False, "Доставка должна провалиться (нет telegram_file_id)"

        actual_status = invoice.status
        await uow.session.commit()

    sessionmaker = get_sessionmaker()
    session = sessionmaker()
    try:
        fresh_invoice = await session.get(Invoice, seeded_invoice_no_file)
        assert fresh_invoice.status == "PAID", (
            "invoice_state_machine.md: провал доставки НЕ должен менять статус инвойса. "
            f"В памяти после вызова статус был '{actual_status}', "
            f"в БД после commit статус стал '{fresh_invoice.status}'."
        )
    finally:
        await session.close()


async def test_delivered_invoice_cannot_be_marked_paid_again(seeded_invoice, mock_bot):
    """
    invoice_state_machine.md Forbidden Transitions: DELIVERED -> PAID запрещён
    (DELIVERED терминален в текущей реализации state machine).
    """
    normalized = make_normalized("ext-race-001")

    first = await process_payment_event(normalized, "cryptobot")
    assert first["status"] == "accepted"

    sessionmaker = get_sessionmaker()
    session = sessionmaker()
    try:
        invoice = await session.get(Invoice, seeded_invoice)
        assert invoice.status == "DELIVERED"
    finally:
        await session.close()

    async with UnitOfWork() as uow:
        invoice = await uow.invoices.get_by_id(seeded_invoice)
        mark_paid_uc = MarkInvoicePaidUseCase(uow)
        ok = await mark_paid_uc.execute(invoice, tx_hash="tx_second_attempt")

        assert ok is False, (
            "State machine обязана запретить DELIVERED -> PAID, "
            "но mark_paid вернул True"
        )
        assert invoice.status == "DELIVERED", "Статус не должен был измениться"
        await uow.session.rollback()


async def test_duplicate_external_payment_id_violates_unique_constraint(seeded_invoice):
    """
    domain_model.md Invoice Invariants: "external_payment_id must be unique."
    Constraint added in migration a7c2e91b4f38 - this test confirms it's
    actually enforced at the DB level, not just assumed.
    """
    from sqlalchemy.exc import IntegrityError

    sessionmaker = get_sessionmaker()
    session = sessionmaker()
    try:
        existing = await session.get(Invoice, seeded_invoice)

        duplicate = Invoice(
            user_id=existing.user_id,
            product_id=existing.product_id,
            amount=existing.amount,
            currency=existing.currency,
            status="PENDING",
            provider=existing.provider,
            external_payment_id=existing.external_payment_id,
            expires_at=existing.expires_at,
        )
        session.add(duplicate)

        try:
            await session.commit()
            assert False, (
                "Ожидался IntegrityError при дублировании external_payment_id, "
                "но INSERT прошёл успешно - unique constraint не работает"
            )
        except IntegrityError:
            await session.rollback()
    finally:
        await session.close()


async def test_delivery_exception_does_not_roll_back_payment_state(seeded_invoice_no_file):
    """
    Regression test for the UoW checkpoint-commit fix (known_issues.md,
    "Already Fixed" section). Before the fix, process_payment_event ran
    PaymentEvent persistence + the PAID transition + delivery inside one
    UnitOfWork with a single commit. An unhandled exception during
    delivery (not just DeliverInvoiceUseCase returning False) propagated
    out of the `async with UnitOfWork()` block, rolling back the WHOLE
    transaction - losing both the PAID transition and the just-persisted
    PaymentEvent. Violated invoice_state_machine.md ("Delivery failure
    does NOT change invoice state") and webhook_idempotency.md ("EVERY
    webhook event must be stored") simultaneously.

    Reproduces the exact real-world trigger found via live BTCPay testnet
    testing: bot_instance.bot is None, so DeliveryService(uow=uow) raises
    RuntimeError("Bot is not initialized") during __init__, before
    DeliverInvoiceUseCase.execute() even runs.
    """
    bot_instance.bot = None  # override autouse mock_bot: simulate uninitialized bot

    normalized = make_normalized("ext-nofile-001")

    result = await process_payment_event(normalized, "cryptobot")

    assert result["status"] == "accepted"

    sessionmaker = get_sessionmaker()
    session = sessionmaker()
    try:
        invoice = await session.get(Invoice, seeded_invoice_no_file)
        assert invoice.status == "PAID", (
            "invoice_state_machine.md: delivery failure (even an "
            "unhandled exception) must NOT roll back the PAID transition. "
            f"Got status '{invoice.status}'."
        )

        event = (await session.execute(
            select(PaymentEvent).where(
                PaymentEvent.invoice_id == seeded_invoice_no_file
            )
        )).scalar_one_or_none()
        assert event is not None, (
            "webhook_idempotency.md: 'EVERY webhook event must be stored.' "
            "The PaymentEvent must survive even when delivery raises."
        )
        assert event.processed is False
        assert event.failed is True
        assert "delivery_exception" in (event.last_error or ""), (
            f"Expected last_error to record the delivery exception, "
            f"got: {event.last_error!r}"
        )
    finally:
        await session.close()
