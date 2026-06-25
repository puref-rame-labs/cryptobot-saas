from app.domain.product.state_machine import ProductState


class PublishProductUseCase:

    def __init__(self, uow):
        self.uow = uow

    async def execute(self, product_id: int):

        product = await self.uow.products.get_by_id(product_id)

        if not product:
            return {"status": "not_found"}

        if product.status == ProductState.READY.value:
            return {"status": "already_ready", "product": product}

        product.status = ProductState.READY.value

        await self.uow.session.flush()

        return {"status": "ok", "product": product}
