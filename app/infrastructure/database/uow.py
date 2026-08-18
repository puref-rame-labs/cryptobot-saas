from app.infrastructure.database.session import get_sessionmaker


class UnitOfWork:
    def __init__(self):
        self._sessionmaker = get_sessionmaker()
        self.session = None

        # repositories (инициализируются после session)
        self.users = None
        self.products = None
        self.categories = None
        self.subcategories = None
        self.product_groups = None
        self.brands = None
        self.invoices = None
        self.payment_events = None
        self.referral_accruals = None

    async def __aenter__(self):
        self.session = self._sessionmaker()

        # repositories bind to session
        from app.infrastructure.repositories.user_repository import UserRepository
        from app.infrastructure.repositories.product_repository import ProductRepository
        from app.infrastructure.repositories.category_repository import CategoryRepository
        from app.infrastructure.repositories.subcategory_repository import SubcategoryRepository
        from app.infrastructure.repositories.product_group_repository import ProductGroupRepository
        from app.infrastructure.repositories.brand_repository import BrandRepository
        from app.infrastructure.repositories.invoice_repository import InvoiceRepository
        from app.infrastructure.repositories.payment_event_repository import PaymentEventRepository
        from app.infrastructure.repositories.referral_accrual_repository import ReferralAccrualRepository

        self.users = UserRepository(self.session)
        self.products = ProductRepository(self.session)
        self.categories = CategoryRepository(self.session)
        self.subcategories = SubcategoryRepository(self.session)
        self.product_groups = ProductGroupRepository(self.session)
        self.brands = BrandRepository(self.session)
        self.invoices = InvoiceRepository(self.session)
        self.payment_events = PaymentEventRepository(self.session)
        self.referral_accruals = ReferralAccrualRepository(self.session)

        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            if exc_type:
                await self.session.rollback()
            else:
                await self.session.commit()
        finally:
            await self.session.close()
