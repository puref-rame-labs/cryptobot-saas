from app.domain.invoice.state_machine import InvoiceState
from app.domain.invoice.invoice_ops import InvoiceOps


class DeliverInvoiceUseCase:

    def __init__(self, delivery_service):
        self.delivery = delivery_service

    async def execute(self, invoice) -> bool:

        # 1. IDEMPOTENCY GUARD (STATE LEVEL)
        if invoice.status == InvoiceState.DELIVERED.value:
            return True

        # 2. DOMAIN VALIDATION (single source of truth)
        if not InvoiceOps.can_deliver(invoice):
            return False

        # 3. SIDE EFFECT
        result = await self.delivery.deliver(
            invoice=invoice,
            user_id=invoice.user.telegram_id,
        )

        # 4. DOMAIN MUTATION
        if result.success:
            InvoiceOps.mark_delivered(invoice)
            return True

        InvoiceOps.mark_failed(invoice)
        return False
