import asyncio
from datetime import datetime, timedelta

from sqlalchemy import select

from app.domain.invoice.state_machine import InvoiceState as InvoiceStatus

from app.infrastructure.database.models import (
    Invoice,
)

from app.infrastructure.database.uow import (
    UnitOfWork,
)

GRACE_PERIOD = timedelta(minutes=5)


async def invoice_expiry_loop():
    try:
        while True:
            async with UnitOfWork() as uow:

                now = datetime.utcnow()
                cutoff = now - GRACE_PERIOD

                stmt = select(Invoice).where(
                    Invoice.status == InvoiceStatus.PENDING,
                    Invoice.expires_at < cutoff,
                )

                result = await uow.session.execute(stmt)
                invoices = result.scalars().all()

                for invoice in invoices:
                    invoice.status = InvoiceStatus.EXPIRED

                await uow.session.commit()

            await asyncio.sleep(30)

    except asyncio.CancelledError:
        return
