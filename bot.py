import os
import re
import asyncio
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram import idle

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
LAST_INDEXED_ID = 1


# Türkçe normalize
def normalize(text):
    text = text.lower()
    text = text.replace("ı", "i").replace("ş", "s")
    text = text.replace("ğ", "g").replace("ü", "u")
    text = text.replace("ö", "o").replace("ç", "c")
    return text


# Markdown link yakalama
def extract_markdown(text):
    pattern = r"\[(.*?)\]\((.*?)\)"
    return re.findall(pattern, text)


# Kanalı ID ile indexle
async def index_channel():
    global LAST_INDEXED_ID

    print("INDEX BAŞLADI")

    last_msg = await app.get_messages(SOURCE_CHANNEL, -1)
    last_msg_id = last_msg.id

    current = LAST_INDEXED_ID

    while current <= last_msg_id:
        try:
            msg = await app.get_messages(SOURCE_CHANNEL, current)
        except:
            current += 1
            continue

        if msg and msg.text:
            links = extract_markdown(msg.text)
            for title, url in links:
                cache.append({
                    "title": title,
                    "url": url
                })

        current += 1

    LAST_INDEXED_ID = last_msg_id + 1
    print(f"Index bitti. Cache: {len(cache)}")

# Yeni mesaj geldiğinde otomatik cache'e ekle
@app.on_message(filters.chat(SOURCE_CHANNEL) & filters.text)
async def auto_add(client, message):
    if message.text:
        links = extract_markdown(message.text)
        for title, url in links:
            cache.append({
                "title": title,
                "url": url
            })
        print("Yeni içerik cache'e eklendi.")


# Tüm gruplarda arama yap
@app.on_message(filters.group & filters.text)
async def search_handler(client, message):
    query = normalize(message.text)

    results = []

    for item in cache:
        if query in normalize(item["title"]):
            results.append(f"[{item['title']}]({item['url']})")

    if results:
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


async def main():
    await app.start()
    await index_channel()
    print("BOT AKTİF")
    await idle()


app.run(main())
