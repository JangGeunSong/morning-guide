import os
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Application, MessageHandler, filters
from apscheduler.schedulers.background import BackgroundScheduler
from openai import OpenAI
import asyncio

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MY_CHAT_ID = os.getenv("MY_CHAT_ID")

openai_client = OpenAI(api_key=OPENAI_API_KEY)

tasks = []

async def handle_message(update, context):
    text = update.message.text
    chat_id = str(update.message.chat_id)
    print(f"Chat ID: {chat_id}")
    tasks.append(text)
    await update.message.reply_text(f"✅ 저장됐어요: {text}\n현재 {len(tasks)}개 등록됨")

def send_morning_guide():
    asyncio.run(_send_morning_guide())

async def _send_morning_guide():
    bot = Bot(token=TELEGRAM_TOKEN)
    if not tasks:
        await bot.send_message(chat_id=MY_CHAT_ID, text="오늘 등록된 할 일이 없어요!")
        return

    task_list = "\n".join([f"{i+1}. {t}" for i, t in enumerate(tasks)])

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "당신은 하루 업무를 효율적으로 도와주는 코치입니다. 친근하고 실용적으로 답해주세요."
            },
            {
                "role": "user",
                "content": f"오늘 해야 할 일 목록입니다:\n{task_list}\n\n각 항목에 대해 수행 순서와 간단한 실행 가이드를 제안해주세요."
            }
        ]
    )

    guide = response.choices[0].message.content
    message = f"🌅 좋은 아침이에요!\n\n📋 오늘 할 일:\n{task_list}\n\n🎯 수행 가이드:\n{guide}"

    await bot.send_message(chat_id=MY_CHAT_ID, text=message)
    tasks.clear()

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        send_morning_guide,
        'cron',
        hour=7,
        minute=0
    )
    scheduler.start()

    print("봇 실행 중...")
    app.run_polling()

if __name__ == "__main__":
    main()