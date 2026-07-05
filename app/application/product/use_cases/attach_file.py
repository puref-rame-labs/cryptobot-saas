from app.domain.product.state_machine import ProductStateMachine, ProductState


class AttachProductFileUseCase:
    def __init__(self, uow):
        self.uow = uow

    async def execute(self, product_id: int, file_id: str, file_type: str):

        product = await self.uow.products.get_by_id(product_id)

        if not product:
            return {"status": "not_found"}

        # GUARD
        if not ProductStateMachine.can_attach(product.status):
            return {
                "status": "invalid_state",
                "reason": f"Cannot attach file in state {product.status}",
            }

        # MUTATION
        product.telegram_file_id = file_id
        product.file_type = file_type

        # STATE TRANSITION
        # DRAFT -> READY (только если был DRAFT)
        if product.status == ProductState.DRAFT.value:
            product.status = ProductStateMachine.mark_ready(product.status)

        await self.uow.session.flush()

        return {
            "status": "ok",
            "product": product,
        }
