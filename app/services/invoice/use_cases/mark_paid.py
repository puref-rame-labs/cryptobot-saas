from app.domain.invoice.invoice_ops import InvoiceOps
from app.domain.invoice.state_machine import InvalidTransition


class MarkInvoicePaidUseCase:
    def __init__(self, uow):
        self.uow = uow

    async def execute(self, invoice, tx_hash: str | None = None) -> bool:

        # 1. DOMAIN MUTATION (with implicit validation via state machine)
        try:
            InvoiceOps.mark_paid(invoice)
        except InvalidTransition:
            return False

        # 2. DOMAIN DATA ENRICHMENT
        if tx_hash and not invoice.tx_hash:
            invoice.tx_hash = tx_hash

        # 3. PERSISTENCE FLUSH (NO COMMIT)
        await self.uow.session.flush()

        return True
