import re
import asyncio
from pyrogram import Client, filters
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from dotenv import load_dotenv
import os

# -----------------------------
# .env yükle
# -----------------------------
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

# -----------------------------
# ÖZEL MESAJDAN DİZİ KAYDETME
# -----------------------------
@app.on_message(filters.private & filters.text)
async def save_series(client, message):
    text = message.text.strip()
    saved_count = 0

    # Yeni format: "Başlık""Link"
    matches = re.findall(r'"(.*?)""(.*?)"', text)
    for title, link in matches:
        title = title.strip()
        link = link.strip()

        # Daha önce kaydedilmiş mi kontrol et
        exists = await collection.find_one({"title": title})
        if exists:
            print(f"[PM] '{title}' zaten kayıtlı, atlandı")
            continue

        markdown_text = f"[{title}]({link})"
        await collection.insert_one({
            "title": title,
            "text": markdown_text,
            "link": link,
            "date": datetime.utcnow()
        })
        print(f"[PM] '{title}' başarıyla kaydedildi")
        saved_count += 1

    if saved_count == 0:
        print(f"[PM] Mesajda kaydedilecek link bulunamadı: {text}")

# -----------------------------
# GRUPTA /ARA KOMUTU
# -----------------------------
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

# -----------------------------
print("[BOT] Bot başlatıldı...")
app.run()
