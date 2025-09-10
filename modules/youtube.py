# === FILE: modules/youtube.py ===
"""
YouTube downloader helper with yt-dlp + FFMPEG support
- Fixes 403 Forbidden by forcing headers & geo_bypass
- Supports COOKIES_FILE env for age/geo restricted videos
"""

import re
import os
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from pyrogram.types import InlineKeyboardMarkup
import yt_dlp

# Detect YouTube URLs
YOUTUBE_REGEX = re.compile(
    r"(https?://)?(www\.)?(m\.)?(youtube\.com|youtu\.be)/"
    r"(watch\?v=[\w\-]{11}|shorts/[\w\-]{11}|embed/[\w\-]{11}|v/[\w\-]{11}|[\w\-]{11})",
    re.IGNORECASE,
)

DOWNLOAD_WORKERS = ThreadPoolExecutor(max_workers=2)

FFMPEG_PATH = os.getenv("FFMPEG_PATH", "ffmpeg")
COOKIES_FILE = os.getenv("COOKIES_FILE", None)


def detect_platform(text: str) -> Optional[str]:
    if text and YOUTUBE_REGEX.search(text):
        return "youtube"
    return None


async def run_blocking(func, *args, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(DOWNLOAD_WORKERS, lambda: func(*args, **kwargs))


def _yt_dlp_download(url: str, mode: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    outtmpl = os.path.join(output_dir, "%(title).50s-%(id)s.%(ext)s")

    ydl_opts = {
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "retries": 5,
        "continuedl": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "ffmpeg_location": FFMPEG_PATH,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    }

    # Use cookies if provided
    if COOKIES_FILE and os.path.exists(COOKIES_FILE):
        ydl_opts["cookiefile"] = COOKIES_FILE

    if mode == "audio":
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })
    else:
        ydl_opts.update({
            "format": "bestvideo[ext=mp4]+bestaudio/best/best",
            "merge_output_format": "mp4",
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except yt_dlp.utils.DownloadError as e:
        raise Exception(f"❌ Download failed: {e}")

    # Find downloaded file
    filepath = None
    if isinstance(info, dict):
        filepath = info.get("_filename") or info.get("requested_downloads", [{}])[0].get("_filename")
    if not filepath:
        files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if os.path.isfile(os.path.join(output_dir, f))]
        if files:
            filepath = max(files, key=os.path.getmtime)

    metadata = {
        "title": info.get("title"),
        "uploader": info.get("uploader"),
        "duration": info.get("duration"),
        "id": info.get("id"),
        "webpage_url": info.get("webpage_url", url),
    }

    return {"filepath": filepath, "metadata": metadata}


async def download_and_send(
    client,
    chat_id: int,
    url: str,
    mode: str,
    requester,
    processing_message,
    developer_markup: InlineKeyboardMarkup,
    downloads_dir: str = "downloads",
):
    start_ts = time.time()
    try:
        res = await run_blocking(_yt_dlp_download, url, mode, downloads_dir)
        filepath = res.get("filepath")
        metadata = res.get("metadata", {})

        if not filepath or not os.path.exists(filepath):
            await client.send_message(chat_id, "❌ Download failed or file not found.")
            await safe_delete(processing_message)
            return

        requester_mention = f"[{escape_md(requester.first_name)}](tg://user?id={requester.id})"
        caption = (
            f"**{escape_md(metadata.get('title') or 'Unknown')}**\n"
            f"Uploader: {escape_md(metadata.get('uploader') or 'Unknown')}\n"
            f"Duration: {format_seconds(metadata.get('duration'))}\n"
            f"Requested by: {requester_mention}\n"
            f"Source: {escape_md(metadata.get('webpage_url'))}"
        )

        if mode == "audio":
            await client.send_audio(
                chat_id,
                audio=filepath,
                caption=caption,
                reply_markup=developer_markup,
                parse_mode="markdown",
            )
        else:
            await client.send_video(
                chat_id,
                video=filepath,
                caption=caption,
                supports_streaming=True,
                reply_markup=developer_markup,
                parse_mode="markdown",
            )

        await safe_delete(processing_message)
        try:
            os.remove(filepath)
        except Exception:
            pass

        elapsed = int(time.time() - start_ts)
        await client.send_message(chat_id, f"✅ Uploaded in {elapsed}s.")

    except Exception as e:
        await safe_delete(processing_message)
        await client.send_message(chat_id, f"❌ Error: {e}")


async def safe_delete(message):
    try:
        if message:
            await message.delete()
    except Exception:
        pass


def format_seconds(seconds):
    try:
        s = int(seconds)
    except Exception:
        return "Unknown"
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def escape_md(text: str) -> str:
    if not text:
        return ""
    for ch in "_`*[]()#:+-=~|{}.!>":
        text = text.replace(ch, f"\\{ch}")
    return text


def register_youtube_handlers(app):
    pass
