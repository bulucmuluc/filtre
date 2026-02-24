import re
import os
import unicodedata
import asyncio
from pyrogram import Client, filters
from dotenv import load_dotenv

load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))

app = Client("matcher_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

channel_cache = {}


# ---------------- NORMALIZE ----------------
def normalize(text):
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("utf-8")
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    return text.strip()


# ---------------- KANAL MESAJINDAN İSİM + LİNK ÇIKAR ----------------
def extract_name_and_link(message):
    raw_text = message.text or message.caption
    if not raw_text:
        return None, None

    # 1️⃣ Markdown formatı
    match = re.search(r"\[(.*?)\]\((.*?)\)", raw_text)
    if match:
        return match.group(1), match.group(2)

    # 2️⃣ Telegram text_link entity
    entities = message.entities or message.caption_entities
    if entities:
        for entity in entities:
            if entity.type == "text_link":
                name = raw_text[entity.offset: entity.offset + entity.length]
                return name, entity.url

    return None, None


# ---------------- BOT BAŞLANGIÇTA KANAL GEÇMİŞİNİ ÇEK ----------------
async def load_channel_history():
    async for message in app.get_chat_history(SOURCE_CHANNEL):
        name, link = extract_name_and_link(message)
        if name and link:
            channel_cache[message.id] = {
                "name": normalize(name),
                "original_name": name,
                "url": link
            }
    print("Kanal cache yüklendi:", len(channel_cache))


# ---------------- SİLME ----------------
async def delete_after_delay(chat_id, bot_msg_id, user_msg_id):
    await asyncio.sleep(600)
    try:
        await app.delete_messages(chat_id, [bot_msg_id, user_msg_id])
    except:
        pass


# ---------------- KANAL YENİ MESAJLARI ----------------
@app.on_message(filters.chat(SOURCE_CHANNEL))
async def cache_new_messages(client, message):
    name, link = extract_name_and_link(message)
    if name and link:
        channel_cache[message.id] = {
            "name": normalize(name),
            "original_name": name,
            "url": link
        }


# ---------------- GRUP DİNLE ----------------
@app.on_message(filters.group & filters.text)
async def group_listener(client, message):

    user_text = normalize(message.text)
    user_words = user_text.split()

    matches = []

    for data in channel_cache.values():
        for word in user_words:
            if word in data["name"]:
                matches.append(data)
                break

    if matches:
        response_text = "Hangisini izlemek istiyorsun?\n\n"

        for item in matches:
            response_text += f"[{item['original_name']}]({item['url']})\n"

        sent = await message.reply(
            response_text,
            disable_web_page_preview=True
        )

        asyncio.create_task(
            delete_after_delay(
                message.chat.id,
                sent.id,
                message.id
            )
        )


# ---------------- ÇALIŞTIR ----------------
async def main():
    await app.start()
    await load_channel_history()
    print("BOT ÇALIŞIYOR")
    await idle()

from pyrogram import idle

app.run(main())
