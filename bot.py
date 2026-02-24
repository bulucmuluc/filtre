import os
import re
import asyncio
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.errors import FloodWait

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
STRING_SESSION = os.getenv("STRING_SESSION")
SOURCE_CHANNEL = os.getenv("SOURCE_CHANNEL")

if SOURCE_CHANNEL.lstrip("-").isdigit():
    SOURCE_CHANNEL = int(SOURCE_CHANNEL)

# ----------------------------
# CLIENTLER
# ----------------------------
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

user = Client(
    "user",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=STRING_SESSION
)

cache = []
indexed_ids = set()

# ----------------------------
# TÜRKÇE NORMALIZE
# ----------------------------
def normalize(text):
    text = text.lower()
    replacements = {
        "ı": "i", "ş": "s", "ğ": "g",
        "ü": "u", "ö": "o", "ç": "c"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

# ----------------------------
# MARKDOWN LINK YAKALAMA
# ----------------------------
def extract_links(message):
    results = []

    if message.entities:
        for entity in message.entities:
            if entity.type == "text_link":
                title = message.text[entity.offset: entity.offset + entity.length]
                url = entity.url
                results.append((title, url))

    pattern = r"\[(.*?)\]\((.*?)\)"
    matches = re.findall(pattern, message.text or "")
    results.extend(matches)

    return results

# ----------------------------
# KANALI INDEXLE (USERBOT)
# ----------------------------
async def index_channel():
    print("Index başlıyor...")

    await user.get_chat(SOURCE_CHANNEL)  # peer resolve fix

    async for msg in user.get_chat_history(SOURCE_CHANNEL):
        if msg.id in indexed_ids:
            continue

        indexed_ids.add(msg.id)

        if msg.text:
            links = extract_links(msg)
            for title, url in links:
                cache.append({
                    "title": title,
                    "url": url
                })

    print("Index tamamlandı. Cache:", len(cache))

# ----------------------------
# YENİ MESAJLARI OTOMATİK CACHE
# ----------------------------
@user.on_message(filters.chat(SOURCE_CHANNEL) & filters.text)
async def auto_cache(_, message):
    if message.id in indexed_ids:
        return

    indexed_ids.add(message.id)

    links = extract_links(message)
    for title, url in links:
        cache.append({
            "title": title,
            "url": url
        })

    print("Yeni içerik eklendi. Cache:", len(cache))

# ----------------------------
# GRUP ARAMA (BOT)
# ----------------------------
@bot.on_message(filters.group & filters.text)
async def search_handler(client, message):

    if not cache:
        return

    query = normalize(message.text)

    results = []

    for item in cache:
        title_norm = normalize(item["title"])

        if query in title_norm or title_norm in query:
            results.append(f"[{item['title']}]({item['url']})")

    if not results:
        return

    text = "Hangisini izlemek istiyorsun?\n\n"
    text += "\n".join(results[:10])

    sent = await message.reply(
        text,
        disable_web_page_preview=True
    )

    # 10 dakika sonra sil
    await asyncio.sleep(600)

    try:
        await sent.delete()
        await message.delete()
    except:
        pass

# ----------------------------
# MAIN
# ----------------------------
async def main():
    await user.start()
    await bot.start()

    print("Userbot + Bot başladı.")

    await index_channel()

    print("Sistem aktif.")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
