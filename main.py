import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from modules.youtube import detect_platform, download_and_send

# =====================
# Telegram Bot Config
# =====================
API_ID = int(os.getenv("API_ID", "123456"))         # ⚠️ Replace or set in Railway
API_HASH = os.getenv("API_HASH", "your_api_hash")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")

app = Client(
    "yt_downloader_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)


# =====================
# START COMMAND
# =====================
@app.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply_text(
        "👋 Hello! Send me a YouTube link and I’ll download it for you.\n\n"
        "👉 Choose whether you want 🎵 audio or 🎬 video.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]]
        ),
    )


# =====================
# YOUTUBE HANDLER
# =====================
@app.on_message(filters.text & ~filters.edited)
async def youtube_handler(client, message):
    url = message.text.strip()
    platform = detect_platform(url)
    if not platform:
        return  # Ignore non-YouTube messages

    # Inline buttons (audio / video)
    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🎵 Audio", callback_data=f"yt_audio|{url}"),
                InlineKeyboardButton("🎬 Video", callback_data=f"yt_video|{url}"),
            ]
        ]
    )

    await message.reply_text(
        "🔽 Select a download option:",
        reply_markup=buttons,
        quote=True,
    )


# =====================
# CALLBACK HANDLER
# =====================
@app.on_callback_query(filters.regex(r"^yt_(audio|video)\|"))
async def callback_handler(client, callback_query):
    data = callback_query.data.split("|")
    mode = data[0].replace("yt_", "")
    url = data[1]

    processing_message = await callback_query.message.reply_text("⏳ Processing your request...")

    await download_and_send(
        client=client,
        chat_id=callback_query.message.chat.id,
        url=url,
        mode=mode,
        requester=callback_query.from_user,
        processing_message=processing_message,
    )


# =====================
# RUN BOT
# =====================
if __name__ == "__main__":
    print("✅ YouTube Downloader Bot is running...")
    app.run()
