"""
Тест всех доступных моделей Gemini.
"""
import os
import sys
import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Фикс кодировки Windows
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Собираем модели
all_models = [m.name for m in client.models.list()]
text_models = [m for m in all_models if "image" not in m.lower() and "tts" not in m.lower() 
               and "audio" not in m.lower() and "live" not in m.lower()
               and ("flash" in m.lower() or "pro" in m.lower())]
image_models = [m for m in all_models if "image" in m.lower()]

print(f"Text models: {len(text_models)}")
print(f"Image models: {len(image_models)}: {image_models}")


async def test_text(name):
    try:
        r = await client.aio.models.generate_content(model=name, contents="Say hello in one word")
        t = r.text.strip()[:40] if r.text else "empty"
        print(f"  OK text: {name} -> {t}")
        return True
    except Exception as e:
        print(f"  FAIL text: {name} -> {str(e)[:100]}")
        return False


async def test_image(name):
    try:
        r = await client.aio.models.generate_content(
            model=name,
            contents="Generate a cute cartoon cat sticker on white background",
            config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
        )
        if r.candidates:
            for part in r.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    print(f"  OK image: {name} -> {len(part.inline_data.data)} bytes")
                    return True
        t = r.text[:60] if r.text else "no text"
        print(f"  WARN image: {name} -> text only: {t}")
        return False
    except Exception as e:
        print(f"  FAIL image: {name} -> {str(e)[:120]}")
        return False


async def main():
    # Тест текста: только самые вероятные
    priority_text = ["models/gemini-2.5-flash", "models/gemini-3.5-flash", "models/gemini-3.6-flash", 
                     "models/gemini-3.7-flash", "models/gemini-3.8-flash", "models/gemini-2.5-pro",
                     "models/gemini-flash-latest", "models/gemini-pro-latest"]
    
    print("\n--- TEXT MODEL TESTS ---")
    ok_text = []
    for m in priority_text:
        if m in text_models:
            if await test_text(m):
                ok_text.append(m)
            await asyncio.sleep(2)

    print("\n--- IMAGE MODEL TESTS ---")
    ok_img = []
    for m in image_models:
        if await test_image(m):
            ok_img.append(m)
        await asyncio.sleep(5)

    print("\n--- RESULTS ---")
    print(f"Working text models: {ok_text}")
    print(f"Working image models: {ok_img}")
    
    if not ok_img:
        print("\nNO IMAGE MODELS WORK!")
        print("Your API key is on FREE TIER for image generation (limit=0).")
        print("Fix: Go to https://aistudio.google.com/apikey -> enable billing")
        print("OR: We can use Pollinations AI (free) + your Gemini for smart prompts")

asyncio.run(main())
