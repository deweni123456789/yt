# === FILE: modules/youtube.py ===
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

# ThreadPool for blocking downloads
DOWNLOAD_WORKERS = ThreadPoolExecutor(max_workers=2)


def detect_platform(text: str) -> Optional[str]:
    if not text:
        return None
    if YOUTUBE_REGEX.search(text):
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
        "retries": 3,
        "continuedl": True,
    }

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

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    filepath = None
    if isinstance(info, dict):
        filepath = info.get("_filename") or info.get("requested_downloads", [{}])[0].get("_filename")
    if not filepath:
        files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if os.path.is]()
