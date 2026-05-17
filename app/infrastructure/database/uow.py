from app.infrastructure.database.session import async_session
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.repositories.product_repository import (
    ProductRepository,
)

class UnitOfWork:
    def __init__(self):
        self.session = None
        self.users = None

    async def __aenter__(self):
        self.session = async_session()
        
        self.users = UserRepository(self.session)

        self.products = ProductRepository(
            self.session
        )
        
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc:
            await self.session.rollback()
        else:
            await self.session.commit()

        await self.session.close()
