import os
import cv2
import tempfile


def extract_frames_from_video(
    video_path: str,
    frame_interval: int = 30,  # каждый 1 сек при 30 fps
    max_frames: int = 10,  # ограничим количество кадров
) -> list[str]:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Не удалось открыть видео: {video_path}")

    temp_dir = tempfile.mkdtemp(prefix="video_frames_")
    frame_paths = []
    frame_count = 0
    saved = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret or saved >= max_frames:
            break

        if frame_count % frame_interval == 0:
            path = os.path.join(temp_dir, f"frame_{saved:03d}.jpg")
            cv2.imwrite(path, frame)
            frame_paths.append(path)
            saved += 1

        frame_count += 1

    cap.release()
    return frame_paths
