import asyncio
import json

from sqlalchemy import select

from app.infrastructure.database.models import PaymentEvent
from app.infrastructure.database.uow import UnitOfWork

from app.services.event_handlers import handle_invoice_paid


async def payment_event_worker():

    while True:

        async with UnitOfWork() as uow:

            stmt = select(PaymentEvent).where(
                PaymentEvent.processed == False,
                PaymentEvent.failed == False,
            )

            result = await uow.session.execute(stmt)
            events = result.scalars().all()

            for event in events:

                if event.event_type != "webhook_received":
                    continue

                try:
                    # 1. deserialize payload (CRITICAL FIX)
                    payload = json.loads(event.payload)

                    # 2. validate minimal required fields
                    invoice_id = payload.get("invoice_id")
                    external_payment_id = payload.get("external_payment_id")
                    tx_hash = payload.get("tx_hash")

                    if not invoice_id or not external_payment_id:
                        raise ValueError("Invalid payload structure")

                    # 3. call handler directly (NO EVENT BUS)
                    await handle_invoice_paid(
                        event=type("Event", (), {
                            "invoice_id": invoice_id,
                            "external_payment_id": external_payment_id,
                            "tx_hash": tx_hash,
                        })()
                    )

                    # 4. mark success
                    event.processed = True
                    event.last_error = None

                except Exception as e:

                    event.retry_count = (event.retry_count or 0) + 1
                    event.last_error = str(e)

                    if event.retry_count >= 3:
                        event.failed = True

                    event.processed = False

            await uow.session.commit()

        await asyncio.sleep(5)
