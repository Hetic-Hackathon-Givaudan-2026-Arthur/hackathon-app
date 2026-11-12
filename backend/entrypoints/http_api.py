from fastapi import FastAPI
from entrypoints.websocket_api import router as websocket_router

app = FastAPI()
app.include_router(websocket_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
