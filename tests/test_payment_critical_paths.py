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
