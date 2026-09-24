import os
import sys
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

async def main():
    print("Testing image generation with billing enabled...")
    
    models_to_test = [
        "gemini-3.1-flash-image",
        "gemini-2.5-flash-image", 
        "gemini-3-pro-image",
    ]
    
    for model in models_to_test:
        print(f"\nTesting {model}...")
        try:
            r = await client.aio.models.generate_content(
                model=model,
                contents="Generate a cute cartoon cat wearing sunglasses, sticker style, solid white background, die-cut, no text",
                config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
            )
            if r.candidates:
                for part in r.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                        size = len(part.inline_data.data)
                        # Сохраняем тестовую картинку
                        with open(f"test_{model.replace('/', '_')}.png", "wb") as f:
                            f.write(part.inline_data.data)
                        print(f"  SUCCESS! {model} -> {size} bytes, saved to file!")
                        return model  # Нашли рабочую модель!
            print(f"  No image returned. Text: {r.text[:100] if r.text else 'None'}")
        except Exception as e:
            print(f"  FAIL: {str(e)[:150]}")
        await asyncio.sleep(3)
    
    print("\nNo working image models found :(")

asyncio.run(main())
