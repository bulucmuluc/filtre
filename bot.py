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

# Mongo bağlantı
mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo["dizi_db"]
collection = db["diziler"]

# ==============================
# ÖZEL MESAJDAN DİZİ KAYDETME
# ==============================
@app.on_message(filters.private & filters.text)
async def save_series(client, message):
    text = message.text

    # Markdown link yakalama
    match = re.search(r"\[(.*?)\]\((.*?)\)", text)
    if not match:
        return await message.reply("⚠️ Geçerli bir markdown link bulunamadı.")

    title = match.group(1)
    link = match.group(2)

    # Aynı başlık varsa ekleme
    exists = await collection.find_one({"title": title})
    if exists:
        return await message.reply("⚠️ Bu dizi zaten kayıtlı.")

    await collection.insert_one({
        "title": title,
        "text": text,
        "link": link,
        "date": datetime.utcnow()
    })

    await message.reply("✅ Dizi başarıyla kaydedildi.")

# ==============================
# GRUPTA /ARA KOMUTU
# ==============================
@app.on_message(filters.command("ara") & filters.group)
async def search_series(client, message):
    if len(message.command) < 2:
        return await message.reply("❗ Kullanım: /ara dizi_adı")

    query = " ".join(message.command[1:])

    results = collection.find({
        "title": {"$regex": query, "$options": "i"}
    })

    response = ""
    async for item in results:
        response += f"{item['text']}\n"

    if not response:
        # Bu yanıt sadece grupta /ara için
        return await message.reply("❌ Sonuç bulunamadı.")

    await message.reply(response, disable_web_page_preview=True)

# ==============================
app.run()
