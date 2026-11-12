from contextlib import asynccontextmanager

from fastapi import FastAPI

from config import load_settings
from entrypoints.http_api import app as http_app
from infrastructure.assets import S3AssetStore
from infrastructure.neon_store import NeonStore


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Connect Neon resources during startup and close them on shutdown."""
    settings = load_settings()
    neon_store = NeonStore(settings.database_url)
    await neon_store.connect()
    asset_store = S3AssetStore(
        endpoint_url=settings.aws_endpoint_url_s3,
        access_key_id=settings.aws_access_key_id,
        secret_access_key=settings.aws_secret_access_key,
        region=settings.aws_region,
        bucket=settings.assets_bucket,
    )
    http_app.state.neon_store = neon_store
    http_app.state.asset_store = asset_store
    try:
        yield
    finally:
        await neon_store.close()


app = FastAPI(lifespan=lifespan)
app.mount("/", http_app)
