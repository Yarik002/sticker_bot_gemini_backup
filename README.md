# AI Sticker Bot (Gemini + Pollinations Free Version) 🎨🤖

This is the legacy/backup version of the AI Sticker Bot. It relies entirely on free image generation tools while using Google Gemini Vision for smart prompt engineering.

## 🌟 Features
- **Smart Vision Prompting**: Uses **Google Gemini Vision** to analyze the user's photo and automatically craft the perfect style prompt.
- **Free Image Generation**: Uses Pollinations AI (FLUX) for cost-free image generation (no API key required).
- **Multiple Styles**: Supports Cartoon, Anime, Chibi, Comic, Pixel Art, and Watercolor.
- **Automated Processing**: Automatically removes backgrounds using Pillow and prepares the image in Telegram's required `.webp` and `.png` sticker formats.
- **In-App Sticker Pack Creation**: Automatically creates and manages Telegram sticker packs via the Telegram Bot API.

## 🛠 Tech Stack
- **Python 3.12**
- **Aiogram 3.x** (Telegram Bot Framework)
- **Google GenAI SDK** (Gemini 2.5 Flash for Vision)
- **Pollinations AI** (Free image generation endpoint)
- **SQLite** (User and balance management)

## 🚀 Setup Instructions

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Set up Environment Variables**:
   Create a `.env` file in the root directory with the following keys:
   ```env
   TELEGRAM_TOKEN=your_telegram_bot_token_here
   GEMINI_API_KEY=your_gemini_api_key_here
   ```
   *(Note: This version does not require a Replicate API token).*

3. **Run the bot**:
   ```bash
   python main.py
   ```
