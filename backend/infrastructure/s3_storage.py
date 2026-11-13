import asyncio
import os

import boto3


class S3ObjectStore:
    """Store and retrieve application data from an S3-compatible endpoint."""

    def __init__(
        self,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        region: str,
    ) -> None:
        """Initialize an S3-compatible client without persisting credentials."""
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region,
            config=boto3.session.Config(s3={"addressing_style": "path"}),
        )

    @classmethod
    def from_env(cls) -> "S3ObjectStore":
        """Build the store from S3 environment variables."""
        values = {
            "endpoint_url": os.environ.get("AWS_ENDPOINT_URL_S3")
            or os.environ.get("WS_ENDPOINT_URL_S3"),
            "access_key_id": os.environ.get("AWS_ACCESS_KEY_ID"),
            "secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY"),
            "region": os.environ.get("AWS_REGION", "eu-central-1"),
        }
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise RuntimeError(
                f"Missing S3 configuration: {', '.join(missing)}"
            )
        return cls(**values)

    async def put_bytes(
        self, bucket: str, key: str, data: bytes, content_type: str
    ) -> None:
        """Persist bytes for images or other application data."""
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    async def get_bytes(self, bucket: str, key: str) -> bytes:
        """Retrieve bytes for an image or another stored object."""
        response = await asyncio.to_thread(
            self._client.get_object,
            Bucket=bucket,
            Key=key,
        )
        return await asyncio.to_thread(response["Body"].read)

    async def list_objects(self, bucket: str, prefix: str = "") -> list[dict]:
        """List objects available under a bucket prefix for catalog searches."""
        def list_all() -> list[dict]:
            """Fetch every page of objects under a bucket prefix."""
            paginator = self._client.get_paginator("list_objects_v2")
            return [
                item
                for page in paginator.paginate(Bucket=bucket, Prefix=prefix)
                for item in page.get("Contents", [])
            ]

        return await asyncio.to_thread(list_all)
