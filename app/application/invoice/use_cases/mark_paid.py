import logging
from decimal import Decimal

from app.domain.invoice.invoice_ops import InvoiceOps
from app.domain.invoice.state_machine import InvalidTransition, InvoiceState

logger = logging.getLogger(__name__)


class MarkInvoicePaidUseCase:
    def __init__(self, uow):
        self.uow = uow

    async def execute(
        self,
        invoice,
        tx_hash: str | None = None,
        paid_asset: str | None = None,
        paid_amount: Decimal | None = None,
        paid_fiat_rate: Decimal | None = None,
    ) -> bool:

        was_expired = invoice.status == InvoiceState.EXPIRED.value

        # 1. DOMAIN MUTATION (with implicit validation via state machine)
        try:
            InvoiceOps.mark_paid(invoice)
        except InvalidTransition:
            return False

        if was_expired:
            logger.warning(
                "Late payment accepted for invoice %s "
                "(was EXPIRED, now PAID, tx_hash=%s)",
                invoice.id,
                tx_hash,
            )

        # 2. DOMAIN DATA ENRICHMENT
        if tx_hash and not invoice.tx_hash:
            invoice.tx_hash = tx_hash

        if paid_asset:
            invoice.paid_asset = paid_asset

        if paid_amount is not None:
            invoice.paid_amount = paid_amount

        if paid_fiat_rate is not None:
            invoice.paid_fiat_rate = paid_fiat_rate

        # 3. PERSISTENCE FLUSH (NO COMMIT)
        await self.uow.session.flush()

        return True
