import asyncio
import logging
import os
import re
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("fb_ig_downloader_bot")

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
VIDEO_DOMAIN_RE = re.compile(
    r"(facebook\.com|fb\.watch|instagram\.com|instagr\.am)",
    re.IGNORECASE,
)
# Đặt giới hạn thấp hơn ngưỡng Telegram để an toàn (MB -> bytes)
MAX_FILESIZE_BYTES = 48 * 1024 * 1024


def validate_env() -> str:
    if not BOT_TOKEN:
        raise RuntimeError(
            "Chưa tìm thấy TELEGRAM_BOT_TOKEN. "
            "Điền vào .env hoặc export TELEGRAM_BOT_TOKEN."
        )
    return BOT_TOKEN


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Gửi URL Facebook hoặc Instagram cho mình, mình sẽ tải video và gửi lại.\n"
        "Giới hạn kích thước ~48MB để phù hợp Telegram."
    )


def is_supported_url(url: str) -> bool:
    return bool(VIDEO_DOMAIN_RE.search(url))


def download_video(url: str, workdir: Path) -> Path:
    """
    Tải video bằng yt-dlp và trả về đường dẫn file.
    Ném DownloadError nếu gặp lỗi.
    """
    ydl_opts = {
        "outtmpl": str(workdir / "video.%(ext)s"),
        "format": "bv*+ba/best",
        "merge_output_format": "mp4",
        "max_filesize": MAX_FILESIZE_BYTES,
        "noplaylist": True,
        "quiet": True,
        "nocheckcertificate": True,
        "geo_bypass": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filepath = Path(ydl.prepare_filename(info)).with_suffix(".mp4")

    if not filepath.exists():
        raise DownloadError(f"Không tìm thấy file sau khi tải: {filepath}")

    if filepath.stat().st_size > MAX_FILESIZE_BYTES:
        raise DownloadError(
            "Video lớn hơn giới hạn gửi file của bot (≈48MB). "
            "Hãy thử link khác hoặc video ngắn hơn."
        )

    return filepath


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message, "update.message phải tồn tại"
    url = update.message.text.strip()

    if not is_supported_url(url):
        await update.message.reply_text(
            "Vui lòng gửi URL Facebook hoặc Instagram hợp lệ."
        )
        return

    progress_msg = await update.message.reply_text("Đang tải video, vui lòng chờ...")

    try:
        async with asyncio.timeout(300):  # 5 phút
            with tempfile.TemporaryDirectory() as tmpdir:
                file_path = await asyncio.to_thread(
                    download_video, url, Path(tmpdir)
                )
                await update.message.reply_video(
                    video=file_path.read_bytes(),
                    caption="✅ Hoàn thành",
                )
    except DownloadError as exc:
        logger.warning("Tải thất bại: %s", exc)
        await update.message.reply_text(
            f"Không tải được video: {exc}"
        )
    except asyncio.TimeoutError:
        await update.message.reply_text("Quá thời gian xử lý, thử lại sau nhé.")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Lỗi không xác định khi xử lý URL")
        await update.message.reply_text(
            f"Bot gặp lỗi: {exc}"
        )
    finally:
        try:
            await progress_msg.delete()
        except Exception:  # noqa: BLE001
            pass


def main() -> None:
    token = validate_env()
    application = (
        Application.builder()
        .token(token)
        .concurrent_updates(True)
        .build()
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_url,
        )
    )

    logger.info("Bot đang chạy. Nhấn Ctrl+C để dừng.")
    application.run_polling(close_loop=False)


if __name__ == "__main__":
    main()

