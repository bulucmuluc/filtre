import re
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from dotenv import load_dotenv

# ================= ENV YÜKLE =================
load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))

app = Client("dizi_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# {"tehran": ["[Tehran](link1)", "[Tehran 2](link2)"]}
dizi_dict = {}


# ================= DİZİ EKLE =================
def add_series(text):
    matches = re.findall(r"\[(.*?)\]\((.*?)\)", text)
    for name, link in matches:
        key = name.lower().strip()
        formatted = f"[{name}]({link})"

        if key not in dizi_dict:
            dizi_dict[key] = []

        if formatted not in dizi_dict[key]:
            dizi_dict[key].append(formatted)
            print(f"[EKLENDİ] {formatted}")


# ================= BAŞLANGIÇ YÜKLE =================
async def load_series():
    dizi_dict.clear()

    async for msg in app.get_chat_history(SOURCE_CHANNEL):
        if msg.text:
            add_series(msg.text)

    print(f"[INIT] Toplam anahtar sayısı: {len(dizi_dict)}")


# ================= KAYNAK KANAL CANLI =================
@app.on_message(filters.chat(SOURCE_CHANNEL) & filters.text)
async def source_listener(client, message: Message):
    add_series(message.text)
    print(f"[YENİ MESAJ - SOURCE] {message.text}")


# ================= TÜM GRUPLARDA ÇALIŞ =================
@app.on_message(filters.group & filters.text)
async def group_listener(client, message: Message):
    text = message.text.lower()
    bulunanlar = []

    for name in dizi_dict:
        if name in text:
            bulunanlar.extend(dizi_dict[name])

    if bulunanlar:
        cevap = "Hangi diziyi izlemek istiyorsun?\n\n"
        cevap += "\n".join(bulunanlar)

        await message.reply_text(
            cevap,
            disable_web_page_preview=True
        )

        print("----- TETİKLENDİ -----")
        print(f"Kullanıcı ID: {message.from_user.id if message.from_user else 'Anonim'}")
        print(f"Grup: {message.chat.title}")
        print(f"Mesaj: {message.text}")
        print("----------------------")


# ================= START =================
app.run(load_series())
