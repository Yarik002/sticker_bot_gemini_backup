import asyncio
import aiohttp
import urllib.parse

async def run():
    prompt = 'Мопс в костюме космонавта на луне'
    style = '2d vector art, die-cut sticker style, solid white background, high quality, flat colors'
    safe_prompt = urllib.parse.quote(f'{prompt}, {style}')
    url = f'https://image.pollinations.ai/prompt/{safe_prompt}?width=512&height=512&nologo=true'
    print(f"Fetching: {url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                print(f"Status: {response.status}")
                data = await response.read()
                print(f"Size: {len(data)} bytes")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(run())
