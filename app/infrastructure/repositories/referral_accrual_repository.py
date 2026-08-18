from sqlalchemy import select, func

from app.infrastructure.database.models import (
    ReferralAccrual,
    ReferralAccrualStatus,
)


class ReferralAccrualRepository:

    def __init__(self, session):

        self.session = session

    async def create_accrual(
        self,
        accrual: ReferralAccrual,
    ):

        self.session.add(accrual)

        await self.session.flush()

        return accrual

    async def get_by_invoice_id(
        self,
        invoice_id: int,
    ):

        stmt = select(ReferralAccrual).where(
            ReferralAccrual.invoice_id == invoice_id
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_summary_for_referrer(
        self,
        referrer_id: int,
    ):

        stmt = (
            select(
                ReferralAccrual.status,
                func.sum(ReferralAccrual.amount),
                func.count(ReferralAccrual.id),
            )
            .where(ReferralAccrual.referrer_id == referrer_id)
            .group_by(ReferralAccrual.status)
        )

        result = await self.session.execute(stmt)

        return result.all()

    async def get_pending_totals_by_referrer(
        self,
    ):

        stmt = (
            select(
                ReferralAccrual.referrer_id,
                func.sum(ReferralAccrual.amount),
                func.count(ReferralAccrual.id),
            )
            .where(
                ReferralAccrual.status
                == ReferralAccrualStatus.PENDING.value
            )
            .group_by(ReferralAccrual.referrer_id)
        )

        result = await self.session.execute(stmt)

        return result.all()

    async def mark_paid_out_for_referrer(
        self,
        referrer_id: int,
    ) -> int:

        stmt = select(ReferralAccrual).where(
            ReferralAccrual.referrer_id == referrer_id,
            ReferralAccrual.status
            == ReferralAccrualStatus.PENDING.value,
        )

        result = await self.session.execute(stmt)
        accruals = result.scalars().all()

        from datetime import datetime

        now = datetime.utcnow()

        for accrual in accruals:
            accrual.status = ReferralAccrualStatus.PAID_OUT.value
            accrual.paid_out_at = now

        await self.session.flush()

        return len(accruals)
