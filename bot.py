import re
import asyncio
from pyrogram import Client, filters
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from dotenv import load_dotenv
import os

# .env yükle
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

app = Client("search_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# MongoDB bağlantısı
mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo["dizi_db"]
collection = db["diziler"]

# ==============================
# ÖZEL MESAJDAN DİZİ KAYDETME (LOGLU)
# ==============================
@app.on_message(filters.private & filters.text)
async def save_series(client, message):
    text = message.text
    print(f"[PM] Yeni mesaj: {text}")  # Terminal log

    # Markdown link yakalama
    match = re.search(r"\[(.*?)\]\((.*?)\)", text)
    if not match:
        print("[PM] Geçersiz format, kaydedilmedi")
        return  # Sessiz geçiş

    title = match.group(1)
    link = match.group(2)

    # Aynı başlık varsa ekleme
    exists = await collection.find_one({"title": title})
    if exists:
        print(f"[PM] '{title}' zaten kayıtlı, atlandı")
        return

    await collection.insert_one({
        "title": title,
        "text": text,
        "link": link,
        "date": datetime.utcnow()
    })
    print(f"[PM] '{title}' başarıyla kaydedildi")

# ==============================
# GRUPTA /ARA KOMUTU (LOGLU)
# ==============================
@app.on_message(filters.command("ara") & filters.group)
async def search_series(client, message):
    if len(message.command) < 2:
        print(f"[GRUP] {message.chat.title}: Hatalı kullanım")
        return await message.reply("❗ Kullanım: /ara dizi_adı")

    query = " ".join(message.command[1:])
    print(f"[GRUP] {message.chat.title}: Arama yapılıyor -> {query}")

    results = collection.find({
        "title": {"$regex": query, "$options": "i"}
    })

    response = ""
    async for item in results:
        response += f"{item['text']}\n"

    if not response:
        print(f"[GRUP] {message.chat.title}: Sonuç bulunamadı")
        return await message.reply("❌ Sonuç bulunamadı.")

    print(f"[GRUP] {message.chat.title}: {len(response.splitlines())} sonuç bulundu")
    await message.reply(response, disable_web_page_preview=True)

app.run()
