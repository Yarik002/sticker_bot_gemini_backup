import os
import io
import logging
import asyncio
from google import genai
from google.genai import types

client: genai.Client = None

# Актуальные модели (сентябрь 2026)
MODEL_VISION = "gemini-3.6-flash"
MODEL_IMAGE_GEN = "gemini-3.1-flash-image"

def init_gemini():
    global client
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        logging.warning("GEMINI_API_KEY не установлен!")
        return
    client = genai.Client(api_key=api_key)
    logging.info(f"Gemini client initialized. Vision: {MODEL_VISION}, ImageGen: {MODEL_IMAGE_GEN}")


async def analyze_photo(photo_bytes: bytes) -> str:
    """Gemini Vision анализирует фото пользователя."""
    try:
        response = await client.aio.models.generate_content(
            model=MODEL_VISION,
            contents=[
                types.Part.from_bytes(data=photo_bytes, mime_type="image/jpeg"),
                "Опиши это изображение максимально подробно на английском языке для художника. "
                "Включи: внешность персонажа (цвет волос, глаз, одежда, аксессуары), позу, выражение лица. "
                "Ответь ТОЛЬКО описанием на английском, без вступления.",
            ],
        )
        return response.text.strip()
    except Exception as e:
        logging.error(f"Gemini Vision error: {e}")
        return "a person"


async def generate_sticker_from_photo(photo_bytes: bytes, style: str) -> bytes | None:
    """
    Отправляет ОРИГИНАЛЬНОЕ фото в Gemini и просит создать стилизованный стикер.
    """
    style_instructions = {
        "cartoon": "Transform this person into a funny CARTOON character (like Pixar/Disney style). Bold outlines, vibrant flat colors, exaggerated cute proportions. Keep recognizable features.",
        "anime": "Transform this person into an ANIME character (Japanese manga/anime style). Big expressive eyes, soft shading, anime hair. Keep recognizable features like hair color and clothing.",
        "chibi": "Transform this person into a CHIBI / KAWAII character. Super-deformed style with an oversized round head, tiny body, huge sparkly eyes. Extremely cute and adorable. Keep recognizable features.",
        "comic": "Transform this person into a COMIC BOOK character (Marvel/DC style). Bold ink outlines, heroic pose, dynamic shading. Keep recognizable features.",
        "pixel": "Transform this person into a PIXEL ART character (16-bit retro video game style). Crisp pixels, retro game aesthetic. Keep recognizable features.",
        "watercolor": "Transform this person into a beautiful WATERCOLOR PORTRAIT. Soft artistic brush strokes, gentle pastel palette, dreamy aesthetic. Keep recognizable features.",
    }

    instruction = style_instructions.get(style, style_instructions["cartoon"])

    prompt = (
        f"{instruction} "
        f"IMPORTANT: Draw ONLY the character on a perfectly SOLID WHITE background (#FFFFFF). "
        f"No text, no border, no shadow, no other objects. Single character, centered, sticker-ready. "
        f"The result must look like a professional die-cut sticker."
    )

    try:
        response = await client.aio.models.generate_content(
            model=MODEL_IMAGE_GEN,
            contents=[
                types.Part.from_bytes(data=photo_bytes, mime_type="image/jpeg"),
                prompt,
            ],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        # Ищем картинку в ответе
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    logging.info(f"Generated sticker style={style}, size={len(part.inline_data.data)} bytes")
                    return part.inline_data.data

        resp_text = response.text[:300] if response.text else "None"
        logging.warning(f"No image in response for style={style}. Text: {resp_text}")
        return None

    except Exception as e:
        logging.error(f"Gemini image gen error ({style}): {e}")
        return None


async def generate_sticker_set(photo_bytes: bytes, styles: list[str]) -> list[tuple[str, bytes]]:
    """Генерирует набор стикеров в разных стилях."""
    results = []
    for style in styles:
        logging.info(f"Generating sticker style: {style}...")
        img_bytes = await generate_sticker_from_photo(photo_bytes, style)
        if img_bytes:
            results.append((style, img_bytes))
        await asyncio.sleep(1)
    return results
