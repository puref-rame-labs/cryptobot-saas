import asyncio
from decimal import Decimal
from types import SimpleNamespace

from sqlalchemy import select, func

from app.application.payments.use_cases.process_payment_event import process_payment_event
from app.infrastructure.database.session import get_sessionmaker
from app.infrastructure.database.models import Invoice, PaymentEvent


def make_normalized(external_payment_id: str):
    return SimpleNamespace(
        external_payment_id=external_payment_id,
        tx_hash="tx_race_test_0001",
        paid_asset="BTC",
        paid_amount=Decimal("0.00123456"),
        paid_fiat_rate=Decimal("8100000.00000000"),
    )


async def test_concurrent_duplicate_webhook_is_idempotent(seeded_invoice, mock_bot):
    normalized = make_normalized("ext-race-001")

    # два "одновременных" вызова с одним и тем же external_payment_id ->
    # одинаковый idempotency_key -> ровно один должен пройти, второй - NO-OP
    results = await asyncio.gather(
        process_payment_event(normalized, "cryptobot"),
        process_payment_event(normalized, "cryptobot"),
    )

    statuses = sorted(r["status"] for r in results)
    assert statuses == ["accepted", "duplicate"], (
        f"Ожидался ровно один 'accepted' и один 'duplicate', получено: {results}"
    )

    sessionmaker = get_sessionmaker()
    session = sessionmaker()
    try:
        invoice = await session.get(Invoice, seeded_invoice)
        assert invoice.status == "DELIVERED", (
            f"Инвойс должен перейти в DELIVERED ровно один раз, "
            f"текущий статус={invoice.status}"
        )
        assert invoice.paid_asset == "BTC"
        assert invoice.paid_amount == Decimal("0.00123456")

        event_count = await session.scalar(
            select(func.count()).select_from(PaymentEvent)
        )
        assert event_count == 1, (
            f"Ожидалась ровно одна запись PaymentEvent, найдено {event_count}"
        )
    finally:
        await session.close()

    assert mock_bot.send_document.await_count == 1, (
        "Доставка должна сработать ровно один раз при конкурентных "
        "дублирующих вебхуках"
    )
