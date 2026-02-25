import os
import asyncio
from pyrogram import Client, filters, idle
from pyrogram.types import Message
from dotenv import load_dotenv

# ================= ENV =================
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
STRING_SESSION = os.getenv("STRING_SESSION")
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))

# 🤖 Bot client (gruplar için)
bot = Client(
    "dizi_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# 👤 Userbot client (geçmiş ve canlı ekleme için)
user = Client(
    "user_session",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=STRING_SESSION
)

# {"tehran": ["[Tehran](link1)", "[Tehran 2](link2)"]}
dizi_dict = {}


# ================= DİZİ EKLEME =================
def add_series(message: Message):
    if not message.text or not message.entities:
        return

    for entity in message.entities:
        if entity.type == "text_link":
            name = message.text[entity.offset: entity.offset + entity.length]
            link = entity.url

            key = name.lower().strip()
            formatted = f"[{name}]({link})"

            if key not in dizi_dict:
                dizi_dict[key] = []

            if formatted not in dizi_dict[key]:
                dizi_dict[key].append(formatted)
                print(f"[EKLENDİ] {formatted}")


# ================= USERBOT - GEÇMİŞ YÜKLE =================
async def load_history():
    print("Geçmiş yükleniyor...")
    async for msg in user.get_chat_history(SOURCE_CHANNEL):
        add_series(msg)
    print(f"Geçmiş yüklendi. Toplam anahtar: {len(dizi_dict)}")


# ================= USERBOT - CANLI DİNLE =================
@user.on_message(filters.chat(SOURCE_CHANNEL))
async def user_source_listener(client, message: Message):
    add_series(message)
    print(f"[YENİ SOURCE] {message.text}")


# ================= BOT - TÜM GRUPLAR =================
@bot.on_message(filters.group & filters.text)
async def group_listener(client, message: Message):
    text = message.text.lower()
    bulunanlar = []

    for name in dizi_dict:
        if name in text:
            bulunanlar.extend(dizi_dict[name])

    if bulunanlar:
        cevap = "Hangi diziyi izlemek istiyorsun?\n\n"
        cevap += "\n".join(bulunanlar)

        await message.reply_text(
            cevap,
            disable_web_page_preview=True
        )

        print("----- TETİKLENDİ -----")
        print(f"Grup: {message.chat.title}")
        print(f"Mesaj: {message.text}")
        print("----------------------")


# ================= MAIN =================
async def main():
    await user.start()
    await bot.start()

    print("Userbot ve Bot başlatıldı.")

    await load_history()

    await idle()  # Botu açık tut


# ================= START =================
asyncio.run(main())
