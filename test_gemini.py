import asyncio
import os
from dotenv import load_dotenv
import logging

load_dotenv()
from services import gemini_ai

async def test_gemini():
    gemini_ai.init_gemini()
    prompt = "Мопс в костюме космонавта на луне"
    print(f"Original: {prompt}")
    res = await gemini_ai.enhance_prompt_for_sticker(prompt)
    print(f"Enhanced: {res}")

if __name__ == "__main__":
    asyncio.run(test_gemini())
