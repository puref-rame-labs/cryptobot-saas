import logging

from app.domain.invoice.state_machine import InvoiceState, InvalidTransition
from app.domain.invoice.invoice_ops import InvoiceOps
from app.infrastructure.database.models import ReferralAccrualStatus

logger = logging.getLogger(__name__)


class RefundInvoiceUseCase:
    """
    refund.md: manual admin-only refund. Transitions PAID or DELIVERED
    -> REFUNDED, and claws back any still-PENDING ReferralAccrual for
    this invoice in the SAME transaction/checkpoint as the REFUNDED
    transition - never a separate best-effort pass.
    """

    def __init__(self, uow):
        self.uow = uow

    async def execute(self, invoice) -> dict:

        if invoice.status not in (
            InvoiceState.PAID.value,
            InvoiceState.DELIVERED.value,
        ):
            return {
                "ok": False,
                "reason": "invalid_status",
                "status": invoice.status,
            }

        # 1. DOMAIN MUTATION (state machine enforces PAID/DELIVERED -> REFUNDED)
        try:
            InvoiceOps.mark_refunded(invoice)
        except InvalidTransition:
            return {
                "ok": False,
                "reason": "invalid_transition",
                "status": invoice.status,
            }

        # 2. REFERRAL ACCRUAL CLAWBACK (refund.md: same transaction,
        # not a separate best-effort step)
        clawback_warning = None

        accrual = await self.uow.referral_accruals.get_by_invoice_id(
            invoice.id
        )

        if accrual:
            if accrual.status == ReferralAccrualStatus.PENDING.value:
                accrual.status = ReferralAccrualStatus.CLAWED_BACK.value
                logger.info(
                    "ReferralAccrual %s clawed back for refunded invoice %s",
                    accrual.id,
                    invoice.id,
                )
            elif accrual.status == ReferralAccrualStatus.PAID_OUT.value:
                clawback_warning = (
                    "Внимание: комиссия уже выплачена рефереру и не может "
                    "быть отозвана автоматически."
                )
                logger.warning(
                    "Invoice %s refunded but ReferralAccrual %s was "
                    "already PAID_OUT - left untouched, flagged for "
                    "manual reconciliation.",
                    invoice.id,
                    accrual.id,
                )

        # 3. PERSISTENCE FLUSH (NO COMMIT - caller controls the checkpoint)
        await self.uow.session.flush()

        return {
            "ok": True,
            "clawback_warning": clawback_warning,
        }
