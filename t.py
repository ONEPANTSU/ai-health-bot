import asyncio
from src.media.s3_client import S3Client


async def main():
    s3 = S3Client()
    s3_key = "t.py"
    await s3.upload_file(s3_key, "test")

asyncio.run(main())