from pyrogram import Client, filters
from pyrogram.enums import ChatAction
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
from pymongo import MongoClient
import asyncio
import aiohttp
import json
import os


# تنظیمات MongoDB
client = MongoClient(MONGO_URL)
db = client.chat_history

# ذخیره محدودیت زمانی کاربران
user_cooldowns = {}

async def check_cooldown(user_id, cooldown_minutes=1):
    if user_id in user_cooldowns:
        last_use = user_cooldowns[user_id]
        if datetime.now() - last_use < timedelta(minutes=cooldown_minutes):
            return False
    user_cooldowns[user_id] = datetime.now()
    return True

async def save_chat_history(user_id, input_text, response):
    try:
        db.conversations.insert_one({
            "user_id": user_id,
            "input": input_text,
            "response": response,
            "timestamp": datetime.now()
        })
    except Exception as e:
        print(f"Error saving to MongoDB: {e}")

async def translate_text(text, target_lang='fa'):
    try:
        translator = GoogleTranslator(source='auto', target=target_lang)
        return translator.translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text

async def get_chatgpt_response(prompt):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data['choices'][0]['message']['content']
            else:
                return None

@app.on_message(filters.command(["start"]))
async def start_command(client, message):
    await message.reply_text(
        "سلام! من یک ربات هوش مصنوعی هستم. برای پرسیدن سوال از دستور /ask استفاده کنید."
    )

@app.on_message(filters.command(["chatgpt", "ai", "ask"]))
async def chatgpt_chat(client, message):
    user_id = message.from_user.id
    
    # بررسی محدودیت زمانی
    if not await check_cooldown(user_id):
        await message.reply_text("لطفا قبل از ارسال درخواست جدید کمی صبر کنید.")
        return

    # بررسی و دریافت ورودی
    if len(message.command) < 2 and not message.reply_to_message:
        await message.reply_text(
            "مثال:\n\n`/ask یک کد ساده وب سایت با HTML، CSS و JS بنویس`"
        )
        return

    if message.reply_to_message and message.reply_to_message.text:
        user_input = message.reply_to_message.text
    else:
        user_input = " ".join(message.command[1:])

    # بررسی طول ورودی
    if len(user_input) > MAX_INPUT_LENGTH:
        await message.reply_text(f"متن ورودی خیلی طولانی است! حداکثر {MAX_INPUT_LENGTH} کاراکتر مجاز است.")
        return

    await client.send_chat_action(message.chat.id, ChatAction.TYPING)

    try:
        # دریافت پاسخ از ChatGPT
        response = await get_chatgpt_response(user_input)
        
        if response:
            # ترجمه پاسخ (اگر نیاز است)
            # translated_response = await translate_text(response)
            
            # ذخیره در دیتابیس
            await save_chat_history(user_id, user_input, response)
            
            # ارسال پاسخ
            await message.reply_text(response)
        else:
            await message.reply_text("متأسفم، نتوانستم پاسخ مناسبی پیدا کنم.")
            
    except Exception as e:
        print(f"Error in chatgpt_chat: {e}")
        await message.reply_text("خطایی در پردازش درخواست شما رخ داد.")

@app.on_message(filters.command(["help"]))
async def help_command(client, message):
    help_text = """
🤖 راهنمای استفاده از ربات:

/ask [سوال] - پرسیدن سوال از هوش مصنوعی
/chatgpt [سوال] - مترادف با دستور ask
/ai [سوال] - مترادف با دستور ask
/help - نمایش این راهنما
/start - شروع مجدد ربات

📝 نکات:
- برای دریافت پاسخ بهتر، سوال خود را واضح و کامل بپرسید
- بین هر درخواست باید کمی صبر کنید
- طول پیام نباید از 500 کاراکتر بیشتر باشد
"""
    await message.reply_text(help_text)
