import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

for model in client.models.list():
    name = model.name
    # Ищем модели для генерации картинок и flash/pro модели
    if "image" in name.lower() or "flash" in name.lower() or "pro" in name.lower() or "imagen" in name.lower():
        methods = getattr(model, 'supported_generation_methods', [])
        print(f"{name}  |  methods: {methods}")
