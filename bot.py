import os
import re
import asyncio
from dotenv import load_dotenv
from pyrogram import Client, filters, idle
from pyrogram.errors import FloodWait

load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))

app = Client(
    "filterbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

cache = []
LAST_INDEXED_ID = 0


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
# Markdown + Entity link yakalama
# -------------------------------------------------
def extract_links(message):
    results = []

    if not message.text:
        return results

    # Entity text_link
    if message.entities:
        for entity in message.entities:
            if entity.type == "text_link":
                title = message.text[entity.offset: entity.offset + entity.length]
                url = entity.url
                results.append((title.strip(), url.strip()))

    # Markdown fallback
    pattern = r"\[(.*?)\]\((.*?)\)"
    matches = re.findall(pattern, message.text)
    for m in matches:
        results.append((m[0].strip(), m[1].strip()))

    return results


# -------------------------------------------------
# Kanalı indexle (SAĞLAM YÖNTEM)
# -------------------------------------------------
async def index_channel():
    global LAST_INDEXED_ID

    print("Index başlıyor...")
    cache.clear()

    async for msg in app.get_chat_history(SOURCE_CHANNEL):
        LAST_INDEXED_ID = max(LAST_INDEXED_ID, msg.id)

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
# Yeni mesaj gelince otomatik cache
# -------------------------------------------------
@app.on_message(filters.chat(SOURCE_CHANNEL) & filters.text)
async def auto_add(client, message):
    global LAST_INDEXED_ID

    if message.id <= LAST_INDEXED_ID:
        return

    LAST_INDEXED_ID = message.id

    links = extract_links(message)

    for title, url in links:
        if not any(x["url"] == url for x in cache):
            cache.append({
                "title": title,
                "url": url
            })

    print("Yeni içerik eklendi. Cache:", len(cache))


# -------------------------------------------------
# Tüm gruplarda arama
# -------------------------------------------------
@app.on_message(filters.group & filters.text)
async def search_handler(client, message):
    if not cache:
        return

    query = normalize(message.text)
    print("Arama:", query, "Cache:", len(cache))

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
    await app.start()
    print("Bot başladı.")
    await index_channel()
    print("Bot aktif.")
    await idle()


app.run(main())
