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
OWNER_ID = int(os.getenv("OWNER_ID"))

app = Client("search_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# MongoDB bağlantısı
mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo["dizi_db"]
collection = db["diziler"]

async def delete_after_delay(client, chat_id, user_msg_id, bot_msg_id):
    await asyncio.sleep(600)
    try:
        await client.delete_messages(chat_id, [user_msg_id, bot_msg_id])
    except:
        pass
# -----------------------------
# ÖZEL MESAJDAN DİZİ KAYDETME (SADECE OWNER)
# -----------------------------
@app.on_message(filters.private & filters.text)
async def save_series(client, message):
    if message.from_user.id != OWNER_ID:
        return

    text = message.text.strip()
    if text.startswith("/"):  # Komutları kaydetme
        return

    saved_count = 0
    matches = re.findall(r'"(.*?)""(.*?)"', text)
    for title, link in matches:
        title = title.strip()
        link = link.strip()

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

    # Argüman yoksa
    if len(message.command) < 2:
        bot_msg = await message.reply(
            "❌ Yanlış komut verdin dostum!\n\nÖrnek Komut:\n`/ara Squid Game`"
        )

        asyncio.create_task(
            delete_after_delay(client, message.chat.id, message.id, bot_msg.id)
        )
        return

    query = " ".join(message.command[1:]).strip()

    # 2 karakterden azsa
    if len(query) < 2:
        bot_msg = await message.reply(
            "❌ Yanlış komut verdin dostum!\n\nÖrnek Komut:\n`/ara Squid Game`"
        )

        asyncio.create_task(
            delete_after_delay(client, message.chat.id, message.id, bot_msg.id)
        )
        return

    results = collection.find({
        "title": {"$regex": query, "$options": "i"}
    })

    response_lines = []
    async for item in results:
        response_lines.append(f"**▪️ {item['text']}**")

    total_results = len(response_lines)

    if total_results == 0:
        response_text = (
            "❌ Sonuç bulunamadı.\n"
            "Eklenmesini istediğin diziyi @diziadmin'e yaz.\n\n"
            "❕Bu Mesaj 10 Dakika Sonra Silinecektir."
        )

        bot_msg = await message.reply(response_text, disable_web_page_preview=True)

        asyncio.create_task(
            delete_after_delay(client, message.chat.id, message.id, bot_msg.id)
        )
        return

    if total_results > 30:
        response_text = (
            "⚠️ Arama yaptığın kelime çok kısa lütfen tam ismini yaz!\n\n"
            "❕Bu Mesaj 10 Dakika Sonra Silinecektir."
        )

        bot_msg = await message.reply(response_text)

        asyncio.create_task(
            delete_after_delay(client, message.chat.id, message.id, bot_msg.id)
        )
        return

    response_text = (
        "**Hangi Diziyi İzlemek İstiyorsun?**\n\n"
        + "\n".join(response_lines)
        + "\n\n❕Bu Mesaj 10 Dakika Sonra Silinecektir."
    )

    bot_msg = await message.reply(response_text, disable_web_page_preview=True)

    asyncio.create_task(
        delete_after_delay(client, message.chat.id, message.id, bot_msg.id)
    )
# -----------------------------
# /filtreler (SADECE OWNER, private)
# -----------------------------
@app.on_message(filters.command("filtreler") & filters.group)
async def list_filters(client, message):
    if message.from_user.id != OWNER_ID:
        return

    results = collection.find({})
    lines = []
    async for item in results:
        lines.append(f"{item['title']} -> {item['link']}")

    if not lines:
        return await message.reply("📂 Hiç filtre yok.")

    text = "\n".join(lines)
    if len(text) > 4000:
        file_path = f"filtreler_{datetime.utcnow().timestamp()}.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)
        await message.reply_document(file_path)
        os.remove(file_path)
    else:
        await message.reply(text)

# -----------------------------
# /sil "filtre ismi" (SADECE OWNER, private)
# -----------------------------
@app.on_message(filters.command("sil") & filters.group)
async def delete_filter(client, message):
    if message.from_user.id != OWNER_ID:
        return

    match = re.search(r'"(.*?)"', message.text)
    if not match:
        return await message.reply("❗ Lütfen filtre adını çift tırnak içinde yazın: /sil \"filtre ismi\"")

    title = match.group(1).strip()
    result = await collection.delete_one({"title": title})
    if result.deleted_count:
        await message.reply(f"✅ '{title}' filtreden silindi.")
    else:
        await message.reply(f"❌ '{title}' bulunamadı.")

# -----------------------------
# /hepsinisil (SADECE OWNER, private)
# -----------------------------
@app.on_message(filters.command("hepsinisil") & filters.group)
async def delete_all_filters(client, message):
    if message.from_user.id != OWNER_ID:
        return

    result = await collection.delete_many({})
    await message.reply(f"✅ Tüm filtreler silindi. ({result.deleted_count} kayıt)")

# -----------------------------
print("[BOT] Bot başlatıldı...")
app.run()
