import asyncio
import os
import urllib.parse
import aiohttp
from io import BytesIO
from aiogram import Bot, Dispatcher
from aiogram.types import BufferedInputFile
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

async def test_bot_send():
    bot = Bot(token=TOKEN)
    
    # Сначала генерируем картинку напрямую, как в image_ai.py
    prompt = 'Мопс в костюме космонавта на луне'
    style = '2d vector art, die-cut sticker style, solid white background, high quality, flat colors'
    safe_prompt = urllib.parse.quote(f'{prompt}, {style}')
    url = f'https://image.pollinations.ai/prompt/{safe_prompt}?width=512&height=512&nologo=true'
    
    print("Fetching image...")
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                image_data = await response.read()
                print(f"Got image: {len(image_data)} bytes")
            else:
                print(f"Failed to get image: {response.status}")
                return
    
    # Теперь пытаемся отправить её. 
    # ВНИМАНИЕ: тут нужен реальный CHAT ID пользователя.
    # Так как мы не знаем CHAT ID (если не посмотреть в БД), мы просто закроем бота.
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(test_bot_send())
