# Bot tải video Facebook/Instagram qua Telegram

Bot nhận URL Facebook hoặc Instagram từ người dùng Telegram, tải video bằng `yt-dlp` và gửi lại video (giới hạn ~48MB để phù hợp với giới hạn Telegram).

## Yêu cầu
- Python 3.10+
- Token bot Telegram

## Cài đặt nhanh
```bash
cd fb-ig-downloader-bot
python -m venv .venv
.venv\Scripts\activate  # trên Windows
pip install -r requirements.txt
```

## Cấu hình
1. Tạo file `.env` (có thể copy từ `example.env`) và điền token bot:
```
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_TOKEN
```
2. Hoặc đặt biến môi trường `TELEGRAM_BOT_TOKEN` trước khi chạy.

## Chạy bot
```bash
python bot.py
```
Gửi URL Facebook/Instagram cho bot. Bot sẽ tải và trả video nếu kích thước phù hợp. Nếu video quá lớn hoặc tải lỗi, bot sẽ báo lại.

## Lưu ý
- Bot đặt giới hạn tải xuống ~48MB để phù hợp giới hạn gửi file của Telegram (bot thường gửi tối đa 50MB). Những video lớn hơn sẽ bị từ chối kèm thông báo.
- Chỉ dùng cho mục đích cá nhân/học tập; hãy tôn trọng bản quyền và điều khoản của nền tảng.

