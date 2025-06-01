import os
import datetime
from typing import Union
from aiofiles import open as aio_open
from aiobotocore.session import get_session

from aiogram.types import BufferedInputFile
from src import config


class S3Client:
    def __init__(self):
        self.endpoint_url = config.S3_URL
        self.access_key = config.S3_ACCESS_KEY
        self.secret_key = config.S3_SECRET_KEY
        self.bucket_name = config.S3_BUCKET
        self.session = get_session()

    async def upload_file(
        self,
        file_path: str,
        username: str,
        filename: Union[str, None] = None,
        date: Union[datetime.datetime, None] = None,
    ) -> str:
        date = date or datetime.datetime.now(datetime.timezone.utc)
        filename = filename or os.path.basename(file_path)
        s3_key = f"{username}/{date:%Y/%m/%d}/{filename}"

        async with self.session.create_client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        ) as client:
            async with aio_open(file_path, "rb") as f:
                data = await f.read()
                await client.put_object(Bucket=self.bucket_name, Key=s3_key, Body=data)

        return f"{self.endpoint_url}/{self.bucket_name}/{s3_key}"

    async def download_file(self, s3_key: str, local_path: str):
        async with self.session.create_client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        ) as client:
            response = await client.get_object(Bucket=self.bucket_name, Key=s3_key)
            async with aio_open(local_path, "wb") as f:
                while True:
                    chunk = await response["Body"].read(1024 * 1024)
                    if not chunk:
                        break
                    await f.write(chunk)

    async def list_objects(self, prefix: str = "") -> list[str]:
        async with self.session.create_client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        ) as client:
            paginator = client.get_paginator("list_objects_v2")
            result = []
            async for page in paginator.paginate(
                Bucket=self.bucket_name, Prefix=prefix
            ):
                for obj in page.get("Contents", []):
                    result.append(obj["Key"])
            return result

    async def get_media_as_buffered_file(self, s3_key: str) -> BufferedInputFile:
        async with self.session.create_client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        ) as client:
            response = await client.get_object(Bucket=self.bucket_name, Key=s3_key)
            data = await response["Body"].read()
            filename = s3_key.split("/")[-1]
            return BufferedInputFile(data, filename=filename)
