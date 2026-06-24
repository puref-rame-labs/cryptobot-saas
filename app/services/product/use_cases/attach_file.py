from app.domain.product.state_machine import ProductStateMachine


class AttachProductFileUseCase:
    """
    Application layer use-case:
    - orchestration only
    - no repository mutation methods
    """

    def __init__(self, uow):
        self.uow = uow

    async def execute(self, product_id: int, file_id: str, file_type: str):

        product = await self.uow.products.get_by_id(product_id)

        if not product:
            return {"status": "not_found"}

        # idempotent update
        product.telegram_file_id = file_id
        product.file_type = file_type

        # domain transition
        product.status = ProductStateMachine.mark_ready(product.status)

        await self.uow.session.flush()

        return {
            "product": product,
            "status": "ok",
        }
