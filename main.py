# === FILE: main.py ===
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from modules import youtube

API_ID = int(os.getenv("API_ID", "123456"))         # add your API_ID
API_HASH = os.getenv("API_HASH", "your_api_hash")   # add your API_HASH
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")

app = Client("yt_dl_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


@app.on_message(filters.text)   # ✅ fixed: removed filters.edited
async def handle_text(client, message):
    text = message.text.strip()
    platform = youtube.detect_platform(text)

    if platform == "youtube":
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎵 Audio", callback_data=f"yt|audio|{text}")],
            [InlineKeyboardButton("🎬 Video", callback_data=f"yt|video|{text}")]
        ])
        await message.reply("🔎 Choose format:", reply_markup=buttons)


@app.on_callback_query()
async def handle_callback(client, callback_query):
    data = callback_query.data.split("|")
    if len(data) != 3:
        return

    platform, mode, url = data
    if platform == "yt":
        processing = await callback_query.message.reply("⏳ Downloading... Please wait")
        dev_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/deweni2")]]
        )
        await youtube.download_and_send(
            client,
            callback_query.message.chat.id,
            url,
            mode,
            callback_query.from_user,
            processing,
            dev_markup
        )
        await callback_query.answer("Done ✅")


if __name__ == "__main__":
    app.run()
