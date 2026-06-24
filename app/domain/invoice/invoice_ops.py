from app.domain.invoice.state_machine import InvoiceStateMachine, InvoiceState


class InvoiceOps:
    """
    Domain mutation layer over Invoice aggregate.
    """

    @staticmethod
    def mark_paid(invoice) -> None:
        invoice.status = InvoiceStateMachine.mark_paid(invoice.status)

    @staticmethod
    def mark_delivered(invoice) -> None:
        invoice.status = InvoiceStateMachine.mark_delivered(invoice.status)

    @staticmethod
    def mark_failed(invoice) -> None:
        invoice.status = InvoiceStateMachine.mark_failed(invoice.status)

    @staticmethod
    def mark_expired(invoice) -> None:
        invoice.status = InvoiceStateMachine.mark_expired(invoice.status)

    @staticmethod
    def is_active(invoice) -> bool:
        return invoice.status in {
            InvoiceState.PENDING.value,
            InvoiceState.PAID.value,
        }

    @staticmethod
    def can_deliver(invoice) -> bool:
        return invoice.status == InvoiceState.PAID.value
