import os
import re
import asyncio
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import Message

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
STRING_SESSION = os.getenv("STRING_SESSION")
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))

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
# REGEX LINK YAKALAMA
# ----------------------------
def extract_links_regex(message: Message):
    text = message.text or message.caption or ""
    pattern = r"\[([^\]]+)\]\((https?://[^\)]+)\)"
    return re.findall(pattern, text)

# ----------------------------
# ENTITY LINK YAKALAMA (ÖNEMLİ)
# ----------------------------
def extract_links_entity(message: Message):
    results = []

    text = message.text or message.caption or ""

    if message.entities:
        for entity in message.entities:
            if entity.type == "text_link":
                start = entity.offset
                end = start + entity.length
                title = text[start:end]
                results.append((title, entity.url))

    if message.caption_entities:
        for entity in message.caption_entities:
            if entity.type == "text_link":
                start = entity.offset
                end = start + entity.length
                title = text[start:end]
                results.append((title, entity.url))

    return results

# ----------------------------
# TÜM LINKLERİ ÇEK
# ----------------------------
def extract_links(message):
    results = []

    text = message.text or message.caption or ""
    if not text:
        return results

    # Sadece markdown formatı: [Başlık](link)
    pattern = r"\[([^\]]+)\]\(([^)]+)\)"

    matches = re.findall(pattern, text)

    for title, url in matches:
        url = url.strip()

        # Eğer http yoksa ekle
        if not url.startswith("http"):
            url = "https://" + url

        results.append((title.strip(), url))

    return results
# ----------------------------
# KANALI INDEXLE
# ----------------------------
async def index_channel():
    print("Index başlıyor...")

    await user.get_chat(SOURCE_CHANNEL)

    async for msg in user.get_chat_history(SOURCE_CHANNEL):

        if msg.id in indexed_ids:
            continue

        indexed_ids.add(msg.id)

        links = extract_links(msg)

        if links:
            print(f"Mesaj {msg.id} bulundu: {links}")

        for title, url in links:
            if not any(x["url"] == url for x in cache):
                cache.append({
                    "title": title.strip(),
                    "url": url.strip()
                })

    print("Index tamamlandı. Cache:", len(cache))

# ----------------------------
# YENİ MESAJLAR OTOMATİK
# ----------------------------
@user.on_message(filters.chat(SOURCE_CHANNEL))
async def auto_cache(_, message):

    if message.id in indexed_ids:
        return

    indexed_ids.add(message.id)

    links = extract_links(message)

    for title, url in links:
        if not any(x["url"] == url for x in cache):
            cache.append({
                "title": title.strip(),
                "url": url.strip()
            })
            print("Yeni içerik eklendi. Cache:", len(cache))

# ----------------------------
# GRUP ARAMA
# ----------------------------
@bot.on_message(filters.group & filters.text)
async def search_handler(client, message):

    if not cache:
        return

    query = normalize(message.text)
    results = []

    for item in cache:
        if query in normalize(item["title"]):
            results.append(f"[{item['title']}]({item['url']})")

    if not results:
        return

    text = "Hangisini izlemek istiyorsun?\n\n"
    text += "\n".join(results[:10])

    sent = await message.reply(
        text,
        disable_web_page_preview=True
    )

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
