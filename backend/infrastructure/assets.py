import asyncio
from typing import Any

import boto3
from botocore.client import Config


class S3AssetStore:
    """Store assets and create temporary download URLs in Neon S3 storage."""

    def __init__(
        self,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        region: str,
        bucket: str,
    ) -> None:
        self._bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    async def put_object(self, key: str, body: bytes | str) -> None:
        """Upload an asset without blocking the async event loop."""
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self._bucket,
            Key=key,
            Body=body,
        )

    async def get_signed_url(self, key: str, expires_in: int = 3600) -> str:
        """Create a temporary URL for reading a stored asset."""
        return await asyncio.to_thread(
            self._client.generate_presigned_url,
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )
