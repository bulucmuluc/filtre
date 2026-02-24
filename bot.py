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
SESSION_STRING = os.getenv("SESSION_STRING")
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))

# USERBOT
user = Client(
    "user_session",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING
)

# BOT
bot = Client(
    "bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

cache = []


# -------------------------------------------------
# Türkçe normalize
# -------------------------------------------------
def normalize(text):
    text = text.lower()
    replacements = {
        "ı": "i", "ş": "s", "ğ": "g",
        "ü": "u", "ö": "o", "ç": "c"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


# -------------------------------------------------
# Markdown link çıkar
# -------------------------------------------------
def extract_links(message):
    results = []

    if not message.text:
        return results

    if message.entities:
        for entity in message.entities:
            if entity.type == "text_link":
                title = message.text[entity.offset: entity.offset + entity.length]
                results.append((title.strip(), entity.url.strip()))

    pattern = r"\[(.*?)\]\((.*?)\)"
    matches = re.findall(pattern, message.text)
    results.extend(matches)

    return results


# -------------------------------------------------
# USERBOT → Kanalı indexle
# -------------------------------------------------
async def index_channel():
    print("Index başlıyor (USERBOT)...")
    cache.clear()

    async for msg in user.get_chat_history(SOURCE_CHANNEL):
        if msg.text:
            links = extract_links(msg)
            for title, url in links:
                if not any(x["url"] == url for x in cache):
                    cache.append({
                        "title": title,
                        "url": url
                    })

    print("Index tamamlandı. Cache:", len(cache))


# -------------------------------------------------
# USERBOT → Yeni mesajları cache ekle
# -------------------------------------------------
@user.on_message(filters.chat(SOURCE_CHANNEL) & filters.text)
async def auto_add(client, message):
    links = extract_links(message)

    for title, url in links:
        if not any(x["url"] == url for x in cache):
            cache.append({
                "title": title,
                "url": url
            })

    print("Yeni içerik eklendi. Cache:", len(cache))


# -------------------------------------------------
# BOT → Gruplarda arama
# -------------------------------------------------
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


# -------------------------------------------------
# MAIN
# -------------------------------------------------
async def main():
    await user.start()
    await bot.start()

    print("Userbot + Bot başladı.")

    await index_channel()

    print("Sistem aktif.")

    await asyncio.Event().wait()


asyncio.run(main())
