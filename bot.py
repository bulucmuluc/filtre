from pyrogram import Client, filters, idle
from pyrogram.types import Message
import os

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")

SOURCE_CHANNEL = -1001694852731  # kendi kanal ID'n

app = Client("bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

CACHE_DB = {}

# ================= LINK OLUŞTUR =================
def build_link(message_id):
    # Private kanal için
    channel_id = str(SOURCE_CHANNEL).replace("-100", "")
    return f"https://t.me/c/{channel_id}/{message_id}"

# ================= CACHE EKLE =================
async def add_to_cache(message: Message):
    if message.text:
        link = build_link(message.id)

        CACHE_DB[message.id] = {
            "text": message.text,
            "link": link
        }

# ================= INDEX =================
async def index_channel():
    print("Index başlıyor...")

    async for msg in app.get_chat_history(SOURCE_CHANNEL):
        await add_to_cache(msg)

    print(f"Index tamamlandı. Toplam: {len(CACHE_DB)} mesaj")

# ================= YENİ MESAJ =================
@app.on_message(filters.chat(SOURCE_CHANNEL))
async def new_message(client, message: Message):
    before = len(CACHE_DB)

    await add_to_cache(message)

    after = len(CACHE_DB)

    print(f"Yeni içerik eklendi. Cache: {after - before}")

# ================= ARAMA =================
@app.on_message(filters.private)
async def search_handler(client, message: Message):
    query = message.text.lower()

    results = []

    for data in CACHE_DB.values():
        if query in data["text"].lower():
            results.append(f"[{data['text'][:40]}...]({data['link']})")

    if not results:
        await message.reply("Sonuç bulunamadı.")
        return

    text = "Hangisini izlemek istiyorsun?\n\n"
    text += "\n".join(results[:10])

    await message.reply(text, disable_web_page_preview=True)

# ================= MAIN =================
async def main():
    await app.start()
    await index_channel()
    print("Bot hazır.")
    await idle()

app.run(main())
