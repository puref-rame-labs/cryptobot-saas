from app.domain.product.state_machine import ProductState
from app.domain.product.state_machine import ProductStateMachine


class PublishProductUseCase:

    def __init__(self, uow):
        self.uow = uow

    async def execute(self, product_id: int):

        product = await self.uow.products.get_by_id(product_id)

        if not product:
            return {"status": "not_found"}

        # idempotent guard
        if product.status == ProductState.PUBLISHED.value:
            return {"status": "already_published", "product": product}

        # strict transition check
        product.status = ProductStateMachine.mark_published(product.status)

        await self.uow.session.flush()

        return {"status": "ok", "product": product}
