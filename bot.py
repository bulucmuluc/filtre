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
@app.on_message(filters.chat(SOURCE_CHANNEL) & filters.text)
async def cache_channel_messages(client, message):

    dizi_ismi = None

    # 1️⃣ Eğer gerçek markdown formatı varsa
    match = re.search(r"\[(.*?)\]\((.*?)\)", message.text or "")
    if match:
        dizi_ismi = match.group(1)

    # 2️⃣ Eğer Telegram text_link entity ise
    elif message.entities:
        for entity in message.entities:
            if entity.type == "text_link":
                dizi_ismi = message.text[entity.offset: entity.offset + entity.length]
                break

    if dizi_ismi:
        channel_cache[message.id] = {
            "name": normalize(dizi_ismi),
            "message_id": message.id
        }

        print("CACHELENDİ:", dizi_ismi)


# ---------------- SİLME ----------------
async def delete_after_delay(client, chat_id, bot_msg_id, user_msg_id):
    await asyncio.sleep(600)

    try:
        await client.delete_messages(chat_id, [bot_msg_id, user_msg_id])
    except Exception as e:
        print("SİLME HATASI:", e)


# ---------------- GRUP DİNLE ----------------
@app.on_message(filters.group & filters.text)
async def group_listener(client, message):

    user_text = normalize(message.text)
    user_words = user_text.split()

    for data in channel_cache.values():
        for word in user_words:
            if word in data["name"]:

                sent = await client.forward_messages(
                    chat_id=message.chat.id,
                    from_chat_id=SOURCE_CHANNEL,
                    message_ids=data["message_id"]
                )

                asyncio.create_task(
                    delete_after_delay(
                        client,
                        message.chat.id,
                        sent.id,
                        message.id
                    )
                )

                return


print("BOT BAŞLADI")
app.run()
