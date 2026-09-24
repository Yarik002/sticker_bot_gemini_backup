import asyncio
import os
import aiohttp
from io import BytesIO
from aiogram import Bot
from aiogram.types import BufferedInputFile
from dotenv import load_dotenv
import urllib.parse

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = 816063676

async def test():
    bot = Bot(token=TOKEN)
    prompt = 'Мопс в костюме космонавта на луне'
    style = '2d vector art, die-cut sticker style, solid white background, high quality, flat colors'
    safe_prompt = urllib.parse.quote(f'{prompt}, {style}')
    url = f'https://image.pollinations.ai/prompt/{safe_prompt}?width=512&height=512&nologo=true'
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            image_data = await response.read()
    
    photo = BufferedInputFile(image_data, filename="sticker.png")
    try:
        await bot.send_photo(
            chat_id=CHAT_ID,
            photo=photo,
            caption="Test Photo"
        )
        print("Success")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(test())
