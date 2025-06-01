import os
import shutil
import datetime
from typing import List

from video_processor import extract_frames_from_video
from src.media.s3_client import S3Client

s3 = S3Client()


async def process_photo_and_upload_to_s3(
    photo_path: str,
    username: str,
    date: datetime.datetime = None,
) -> str:
    date = date or datetime.datetime.now(datetime.timezone.utc)
    filename = os.path.basename(photo_path)

    url = await s3.upload_file(
        file_path=photo_path,
        username=username,
        filename=filename,
        date=date,
    )

    # удаляем локальный файл
    try:
        os.remove(photo_path)
    except FileNotFoundError:
        pass

    return url


async def process_video_and_upload_to_s3(
    video_path: str,
    username: str,
    date: datetime.datetime = None,
    frame_interval: int = 30,
    max_frames: int = 10,
) -> List[str]:
    date = date or datetime.datetime.now(datetime.timezone.utc)

    # извлекаем кадры
    frame_paths = extract_frames_from_video(
        video_path, frame_interval=frame_interval, max_frames=max_frames
    )

    s3_urls = []
    for frame_path in frame_paths:
        filename = os.path.basename(frame_path)
        url = await s3.upload_file(
            file_path=frame_path, username=username, filename=filename, date=date
        )
        s3_urls.append(url)

    # удаляем видеофайл и папку с кадрами
    try:
        os.remove(video_path)
    except FileNotFoundError:
        pass

    temp_dir = os.path.dirname(frame_paths[0]) if frame_paths else None
    if temp_dir and os.path.isdir(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)

    return s3_urls
