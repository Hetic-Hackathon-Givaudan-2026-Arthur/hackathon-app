from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from entrypoints.websocket_api import router as websocket_router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(websocket_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
