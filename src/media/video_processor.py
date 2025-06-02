import os
import math
import tempfile
import subprocess
from datetime import datetime
from src.media.s3_client import S3Client


s3_client = S3Client()


async def extract_contact_sheet_and_upload(
    video_path: str, video_name: str, username: str, max_frames: int = 120
) -> str:
    # Получаем длительность видео
    cmd_duration = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    result = subprocess.run(
        cmd_duration, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    duration = float(result.stdout.strip())

    # Расчёт fps для нужного числа кадров
    fps = max_frames / duration  # например, 12 кадров за всё видео

    # Размер сетки (например, 3x4 для 12 кадров)
    rows = math.ceil(math.sqrt(max_frames))
    cols = math.ceil(max_frames / rows)
    tile = f"{cols}x{rows}"

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "contact_sheet.jpg")
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-vf",
            f"fps={fps},scale=320:-1,tile={tile}",
            output_path,
        ]
        subprocess.run(cmd, check=True)

        s3_key = await s3_client.upload_file(
            file_path=output_path,
            username=username,
            filename=f"{video_name}_contact_sheet.jpg",
            date=datetime.utcnow(),
        )
        return s3_key
