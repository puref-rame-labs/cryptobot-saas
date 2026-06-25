from app.domain.product.state_machine import ProductState
from app.domain.product.state_machine import ProductStateMachine


class AttachProductFileUseCase:

    def __init__(self, uow):
        self.uow = uow

    async def execute(self, product_id: int, file_id: str, file_type: str):

        product = await self.uow.products.get_by_id(product_id)

        if not product:
            return {"status": "not_found"}

        product.telegram_file_id = file_id
        product.file_type = file_type

        current = product.status
        target = ProductState.READY.value

        if current != target:
            product.status = ProductStateMachine.mark_ready(current)

        await self.uow.session.flush()

        return {
            "status": "ok",
            "product": product,
        }
