import asyncio
import logging
import os
import traceback
import time
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message, CallbackQuery, BufferedInputFile,
    InlineKeyboardMarkup, InlineKeyboardButton, InputSticker
)

import database
from services import gemini_ai, image_processor

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(level=logging.INFO)

dp = Dispatcher()
bot: Bot = None

# Доступные стили стикеров
STYLES = {
    "cartoon":    "🎨 Мультяшный",
    "anime":      "🌸 Аниме",
    "chibi":      "🧸 Чиби (Каваий)",
    "comic":      "💥 Комикс",
    "pixel":      "👾 Пиксельный",
    "watercolor": "🎨 Акварель",
}

# Временное хранилище фото пользователей
user_sessions = {}


def styles_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for style_id, style_name in STYLES.items():
        buttons.append([InlineKeyboardButton(text=style_name, callback_data=f"style:{style_id}")])
    buttons.append([InlineKeyboardButton(text="🎁 ВСЕ СТИЛИ (6 стикеров)", callback_data="style:all")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ──────────────────────────── /start ────────────────────────────

@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or "User"
    await database.add_user(user_id, username)
    user = await database.get_user(user_id)
    balance = user["balance"] if user else 0

    text = (
        f"Привет, {username}! 🎨\n\n"
        f"Я — <b>AI Sticker Creator</b>. Я создаю профессиональные стикер-паки из твоих фотографий!\n\n"
        f"📸 <b>Как это работает:</b>\n"
        f"1. Отправь мне любое фото (селфи, питомец, друг)\n"
        f"2. Выбери стиль (мультяшный, аниме, чиби...)\n"
        f"3. Получи готовый стикер-пак!\n\n"
        f"🎁 У тебя <b>{balance}</b> бесплатных генераций.\n\n"
        f"Просто скинь мне фото! 👇"
    )
    await message.answer(text, parse_mode="HTML")


# ──────────────────────────── Приём фото ────────────────────────────

@dp.message(F.photo)
async def handle_photo(message: Message):
    user_id = message.from_user.id
    user = await database.get_user(user_id)

    if not user:
        await database.add_user(user_id, message.from_user.username or "User")
        user = await database.get_user(user_id)

    if user["balance"] <= 0:
        await message.answer(
            "😢 У тебя закончились бесплатные генерации.\n"
            "Скоро здесь будет кнопка покупки — следи за обновлениями!"
        )
        return

    msg = await message.answer("📸 Получил фото! Анализирую с помощью ИИ...")

    try:
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        photo_bytes_io = await bot.download_file(file.file_path)
        photo_bytes = photo_bytes_io.read()

        # Анализируем фото через Gemini Vision
        description = await gemini_ai.analyze_photo(photo_bytes)
        logging.info(f"Photo analysis for user {user_id}: {description[:200]}")

        # Сохраняем фото в сессию (оригинальные байты!)
        user_sessions[user_id] = {
            "description": description,
            "photo_bytes": photo_bytes,
        }

        await msg.edit_text(
            f"✅ Фото проанализировано!\n\n"
            f"🤖 <b>ИИ видит:</b> <i>{description[:250]}...</i>\n\n"
            f"Теперь выбери стиль для стикер-пака: 👇",
            parse_mode="HTML",
            reply_markup=styles_keyboard(),
        )

    except Exception as e:
        logging.error(f"Photo handling error: {traceback.format_exc()}")
        await msg.edit_text(f"❌ Ошибка при анализе фото:\n<code>{e}</code>", parse_mode="HTML")


# ──────────────────────────── Выбор стиля ────────────────────────────

@dp.callback_query(F.data.startswith("style:"))
async def handle_style_choice(callback: CallbackQuery):
    user_id = callback.from_user.id
    style_choice = callback.data.split(":")[1]

    if user_id not in user_sessions:
        await callback.answer("⚠️ Сессия истекла. Отправь фото ещё раз!", show_alert=True)
        return

    session = user_sessions[user_id]
    photo_bytes = session["photo_bytes"]

    if style_choice == "all":
        styles_to_generate = list(STYLES.keys())
    else:
        styles_to_generate = [style_choice]

    await callback.answer()
    
    count = len(styles_to_generate)
    msg = await callback.message.edit_text(
        f"🎨 Генерирую {'стикер-пак из ' + str(count) + ' стикеров' if count > 1 else '1 стикер'}...\n"
        f"⏳ Это займёт 20-60 секунд. Gemini рисует шедевры!"
    )

    try:
        # Отправляем ОРИГИНАЛЬНОЕ ФОТО в Gemini для стилизации
        sticker_results = await gemini_ai.generate_sticker_set(photo_bytes, styles_to_generate)

        if not sticker_results:
            await msg.edit_text(
                "😢 Не удалось сгенерировать стикеры. Попробуй другое фото!\n"
                "(Проверь логи в терминале для деталей ошибки)"
            )
            return

        await msg.edit_text(f"✂️ Обрабатываю {len(sticker_results)} стикеров...")

        # Обрабатываем каждый стикер
        processed_stickers = []
        for style_name, img_bytes in sticker_results:
            sticker_webp = await image_processor.process_sticker(img_bytes)
            sticker_png = await image_processor.process_sticker_png(img_bytes)
            processed_stickers.append((style_name, sticker_webp, sticker_png))

        # ─── Создаём стикер-пак в Telegram ───
        bot_info = await bot.get_me()
        bot_username = bot_info.username
        pack_id = f"p{user_id}_{int(time.time())}"
        pack_name = f"{pack_id}_by_{bot_username}"
        pack_title = f"🎨 AI Stickers — {callback.from_user.first_name or 'User'}"

        first_style, first_webp, first_png = processed_stickers[0]
        emojis_map = {
            "cartoon": "😄", "anime": "🌸", "chibi": "🥺",
            "comic": "💥", "pixel": "👾", "watercolor": "🎨",
        }

        first_input = InputSticker(
            sticker=BufferedInputFile(first_png, filename="s0.png"),
            emoji_list=[emojis_map.get(first_style, "😎")],
            format="static",
        )

        pack_created = False
        try:
            await bot.create_new_sticker_set(
                user_id=user_id,
                name=pack_name,
                title=pack_title,
                stickers=[first_input],
            )
            pack_created = True
            logging.info(f"Created sticker pack: {pack_name}")
        except Exception as e:
            logging.error(f"Create sticker set error: {e}")

        if pack_created:
            # Добавляем остальные стикеры
            for i, (sn, sw, sp) in enumerate(processed_stickers[1:], start=1):
                try:
                    s = InputSticker(
                        sticker=BufferedInputFile(sp, filename=f"s{i}.png"),
                        emoji_list=[emojis_map.get(sn, "😎")],
                        format="static",
                    )
                    await bot.add_sticker_to_set(user_id=user_id, name=pack_name, sticker=s)
                except Exception as e:
                    logging.warning(f"Add sticker {i} error: {e}")

            await database.decrease_balance(user_id)
            await database.save_sticker_pack(user_id, pack_name, pack_title, len(processed_stickers))
            new_balance = (await database.get_user(user_id))["balance"]

            pack_url = f"https://t.me/addstickers/{pack_name}"
            await msg.edit_text(
                f"✅ <b>Стикер-пак готов!</b>\n\n"
                f"📦 <b>{len(processed_stickers)}</b> стикеров в паке\n"
                f"🔗 <a href='{pack_url}'>👉 Добавить стикер-пак</a>\n\n"
                f"Осталось генераций: <b>{new_balance}</b>\n\n"
                f"📸 Отправь ещё фото для нового пака!",
                parse_mode="HTML",
            )
        else:
            # Фоллбэк: отправляем стикеры по одному
            for sn, sw, sp in processed_stickers:
                sf = BufferedInputFile(sw, filename=f"sticker_{sn}.webp")
                await callback.message.answer_sticker(sticker=sf)

            await database.decrease_balance(user_id)
            new_balance = (await database.get_user(user_id))["balance"]
            await msg.edit_text(
                f"✅ {len(processed_stickers)} стикеров отправлено (без пака).\n"
                f"Осталось генераций: {new_balance}"
            )

        user_sessions.pop(user_id, None)

    except Exception as e:
        logging.error(f"Generation error: {traceback.format_exc()}")
        await msg.edit_text(
            f"❌ Ошибка генерации:\n<code>{e}</code>",
            parse_mode="HTML",
        )


# ──────────────────────────── Текст без фото ────────────────────────────

@dp.message(F.text)
async def handle_text(message: Message):
    if message.text.startswith("/"):
        return
    await message.answer(
        "📸 Отправь мне <b>фотографию</b>, чтобы создать стикер-пак!",
        parse_mode="HTML",
    )


# ──────────────────────────── Main ────────────────────────────

async def main():
    global bot

    if not TOKEN or TOKEN == "your_telegram_bot_token_here":
        logging.error("TELEGRAM_TOKEN не установлен в .env!")
        return

    bot = Bot(token=TOKEN)
    gemini_ai.init_gemini()
    await database.init_db()

    logging.info("🚀 Bot started! Waiting for photos...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
