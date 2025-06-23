import logging


async def handle_video_exception(e, message):
    if "file is too big" in str(e):
        await message.answer("""
    📏 <strong>Размер видео превышает 20 МБ.</strong>\n
    Пожалуйста, уменьшите размер файла, например, используя один из следующих онлайн-инструментов:
    - <a href="https://www.freeconvert.com/video-compressor" target="_blank">FreeConvert</a>
    - <a href="https://www.compress2go.com/compress-video" target="_blank">Compress2Go</a>
    - <a href="https://www.capcut.com/tools/free-video-compressor" target="_blank">CapCut</a>
    После сжатия отправьте видео снова, и я с радостью продолжу обработку.
                """)
    else:
        await message.answer("❌ Ошибка при сохранении видео")
    logging.error(f"Error: {e}")