from fastapi import FastAPI

from app.api.routes.payment_webhook import (
    router as payment_router,
)

app = FastAPI()

app.include_router(
    payment_router,
    prefix="/webhook",
)


@app.get("/health")
async def health():

    return {
        "status": "ok"
    }
