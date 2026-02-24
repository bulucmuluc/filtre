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


# ---------------- KANAL CACHE ----------------
@app.on_message(filters.chat(SOURCE_CHANNEL))
async def cache_channel_messages(client, message):

    raw_text = message.text or message.caption
    if not raw_text:
        return

    match = re.search(r"\[(.*?)\]\((.*?)\)", raw_text)

    if match:
        dizi_ismi = match.group(1)
        link = match.group(2)

        channel_cache[message.id] = {
            "name": normalize(dizi_ismi),
            "original_name": dizi_ismi,
            "url": link
        }

        print("CACHELENDİ:", dizi_ismi)


# ---------------- SİLME ----------------
async def delete_after_delay(client, chat_id, bot_msg_id, user_msg_id):
    await asyncio.sleep(600)
    try:
        await client.delete_messages(chat_id, [bot_msg_id, user_msg_id])
    except:
        pass


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
                client,
                message.chat.id,
                sent.id,
                message.id
            )
        )


print("BOT BAŞLADI")
app.run()
