import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Expose the backend connection settings loaded from environment variables."""

    database_url: str
    aws_endpoint_url_s3: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    assets_bucket: str = "assets"


def load_settings() -> Settings:
    """Load required Neon and S3-compatible storage settings."""
    required = {
        "DATABASE_URL": os.getenv("DATABASE_URL"),
        "AWS_ENDPOINT_URL_S3": os.getenv("AWS_ENDPOINT_URL_S3"),
        "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID"),
        "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "AWS_REGION": os.getenv("AWS_REGION"),
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(f"Missing backend environment variables: {', '.join(missing)}")

    return Settings(
        database_url=required["DATABASE_URL"],
        aws_endpoint_url_s3=required["AWS_ENDPOINT_URL_S3"],
        aws_access_key_id=required["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=required["AWS_SECRET_ACCESS_KEY"],
        aws_region=required["AWS_REGION"],
        assets_bucket=os.getenv("ASSETS_BUCKET", "assets"),
    )
