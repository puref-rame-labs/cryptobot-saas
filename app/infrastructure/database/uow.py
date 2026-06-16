from app.infrastructure.database.session import get_sessionmaker


class UnitOfWork:
    def __init__(self):
        self._sessionmaker = get_sessionmaker()
        self.session = None

        # repositories (инициализируются после session)
        self.users = None
        self.products = None
        self.invoices = None
        self.payment_events = None

    async def __aenter__(self):
        self.session = self._sessionmaker()

        # repositories bind to session
        from app.infrastructure.repositories.user_repository import UserRepository
        from app.infrastructure.repositories.product_repository import ProductRepository
        from app.infrastructure.repositories.invoice_repository import InvoiceRepository
        from app.infrastructure.repositories.payment_event_repository import PaymentEventRepository

        self.users = UserRepository(self.session)
        self.products = ProductRepository(self.session)
        self.invoices = InvoiceRepository(self.session)
        self.payment_events = PaymentEventRepository(self.session)

        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            if exc_type:
                await self.session.rollback()
            else:
                await self.session.commit()
        finally:
            await self.session.close()
