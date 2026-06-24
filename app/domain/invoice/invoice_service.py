from app.domain.invoice.invoice_ops import InvoiceOps
from app.domain.invoice.state_machine import InvalidTransition


class InvoiceDomainService:
    """
    Orchestration domain layer.
    Управляет бизнес-переходами, но не I/O.
    """

    def pay(self, invoice, tx_hash: str | None = None):
        try:
            InvoiceOps.mark_paid(invoice)

            if tx_hash and not invoice.tx_hash:
                invoice.tx_hash = tx_hash

            return True

        except InvalidTransition:
            return False

    def deliver(self, invoice):
        try:
            InvoiceOps.mark_delivered(invoice)
            return True
        except InvalidTransition:
            return False

    def fail(self, invoice):
        try:
            InvoiceOps.mark_failed(invoice)
            return True
        except InvalidTransition:
            return False

    def expire(self, invoice):
        try:
            InvoiceOps.mark_expired(invoice)
            return True
        except InvalidTransition:
            return False
