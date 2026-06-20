import telebot
from PIL import Image
import os

TOKEN = os.environ.get("BOT_TOKEN")
# گرفتن آیدی ادمین از متغیرهای Railway (اگه نبود 0 در نظر میگیره)
ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))

if not TOKEN:
    raise ValueError("❌ لطفاً BOT_TOKEN را تنظیم کنید!")

bot = telebot.TeleBot(TOKEN)
WATERMARK_PATH = "tag_image.png" 

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id

    # ۱. بخش مخصوص ادمین: اگر ادمین عکس را با کپشن /set_tag بفرستد
    if chat_id == ADMIN_ID and message.caption == '/set_tag':
        status_msg = bot.reply_to(message, "در حال ذخیره واترمارک جدید...")
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # ذخیره و جایگزینی عکس واترمارک
            with open(WATERMARK_PATH, 'wb') as new_tag:
                new_tag.write(downloaded_file)
                
            bot.edit_message_text("✅ واترمارک جدید با موفقیت ذخیره شد و روی عکس‌های بعدی اعمال می‌شود.", chat_id, status_msg.message_id)
        except Exception as e:
            bot.edit_message_text(f"❌ خطا در ذخیره واترمارک: {e}", chat_id, status_msg.message_id)
        return # خروج از تابع تا عکس رو به عنوان عکس معمولی پردازش نکنه

    # ۲. بررسی اینکه آیا اصلاً واترمارکی وجود دارد؟
    if not os.path.exists(WATERMARK_PATH):
        bot.reply_to(message, "⚠️ واترمارکی یافت نشد! لطفاً ادمین ابتدا یک واترمارک تنظیم کند.")
        return

    # ۳. پردازش عکس کاربران (مثل قبل)
    status_msg = bot.reply_to(message, "⏳ در حال پردازش عکس...")
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        input_path = f"input_{chat_id}.jpg"
        output_path = f"output_{chat_id}.jpg"

        with open(input_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        base_image = Image.open(input_path).convert("RGBA")
        watermark = Image.open(WATERMARK_PATH).convert("RGBA")

        x = base_image.width - watermark.width - 20
        y = base_image.height - watermark.height - 20
        
        transparent = Image.new('RGBA', base_image.size, (0,0,0,0))
        transparent.paste(base_image, (0,0))
        transparent.paste(watermark, (x, y), mask=watermark)
        
        final_image = transparent.convert("RGB")
        final_image.save(output_path, "JPEG")

        with open(output_path, 'rb') as photo_to_send:
            bot.send_photo(chat_id, photo_to_send)

        os.remove(input_path)
        os.remove(output_path)
        bot.delete_message(chat_id, status_msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ خطایی رخ داد: {e}", chat_id, status_msg.message_id)

if __name__ == "__main__":
    print("Bot is up and running...")
    bot.infinity_polling()
