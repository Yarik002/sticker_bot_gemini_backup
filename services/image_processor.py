import io
import asyncio
from PIL import Image


def _remove_white_bg(image_bytes: bytes) -> bytes:
    """Убирает белый фон и делает его прозрачным."""
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    pixels = img.load()
    w, h = img.size

    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            # Если пиксель близок к белому — делаем прозрачным
            if r > 235 and g > 235 and b > 235:
                pixels[x, y] = (255, 255, 255, 0)

    return _to_webp(img)


def _to_webp(img: Image.Image) -> bytes:
    """Ресайзит картинку до 512x512 и конвертирует в WEBP для Telegram."""
    # Телеграм требует: одна сторона = 512, вторая <= 512
    img.thumbnail((512, 512), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    img.save(output, format="WEBP", quality=95)
    return output.getvalue()


def _to_png(img: Image.Image) -> bytes:
    """Ресайзит и конвертирует в PNG (для создания стикер-сетов)."""
    img.thumbnail((512, 512), Image.Resampling.LANCZOS)
    output = io.BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()


async def process_sticker(image_bytes: bytes) -> bytes:
    """
    Обработка картинки для стикера:
    1. Удаление белого фона
    2. Ресайз до 512x512
    3. Конвертация в WEBP
    """
    return await asyncio.to_thread(_remove_white_bg, image_bytes)


async def process_sticker_png(image_bytes: bytes) -> bytes:
    """
    Обработка картинки для стикер-пака (PNG формат для createNewStickerSet).
    """
    def _process(data: bytes) -> bytes:
        img = Image.open(io.BytesIO(data)).convert("RGBA")
        pixels = img.load()
        w, h = img.size
        for y in range(h):
            for x in range(w):
                r, g, b, a = pixels[x, y]
                if r > 235 and g > 235 and b > 235:
                    pixels[x, y] = (255, 255, 255, 0)
        return _to_png(img)

    return await asyncio.to_thread(_process, data=image_bytes)
