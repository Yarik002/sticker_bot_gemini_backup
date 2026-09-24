import aiohttp
import urllib.parse
from io import BytesIO

async def generate_image(prompt: str) -> BytesIO:
    """
    Генерирует картинку через Pollinations AI. 
    Это абсолютно бесплатный сервис (не требует ключей), идеален для старта и тестов.
    """
    # Добавляем промпт-хаки, чтобы картинка была похожа на стикер
    style = "2d vector art, die-cut sticker style, solid white background, high quality, flat colors"
    safe_prompt = urllib.parse.quote(f"{prompt}, {style}")
    
    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=512&height=512&nologo=true"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                image_data = await response.read()
                return BytesIO(image_data)
            else:
                raise Exception(f"Ошибка сервера картинок: {response.status}")
