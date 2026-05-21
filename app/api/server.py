import uvicorn


async def run_api():

    config = uvicorn.Config(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )

    server = uvicorn.Server(config)

    await server.serve()
