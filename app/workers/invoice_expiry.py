import asyncio
from datetime import datetime

from sqlalchemy import select

from app.domain.invoice.state_machine import InvoiceState as InvoiceStatus

from app.infrastructure.database.models import (
    Invoice,
)

from app.infrastructure.database.uow import (
    UnitOfWork,
)


async def invoice_expiry_loop():
    try:
        while True:
            async with UnitOfWork() as uow:

                stmt = select(Invoice).where(
                    Invoice.status == InvoiceStatus.PENDING
                )

                result = await uow.session.execute(stmt)
                invoices = result.scalars().all()

                now = datetime.utcnow()

                for invoice in invoices:
                    if invoice.expires_at < now:
                        invoice.status = InvoiceStatus.EXPIRED

                await uow.session.commit()

            await asyncio.sleep(30)

    except asyncio.CancelledError:
        return
