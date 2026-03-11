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
                "content": """당신은 6년 차 SI/SM 개발자이자 팀 리드인 사용자의 '비즈니스 가속화 코치'입니다.
                사용자는 일반론을 혐오하며, 즉각적인 실행(Execution)과 수익화(SaaS 빌딩)에 미쳐 있습니다.

                [가이드 작성 엄격 규칙]
                1. 전문가적 권위: '안녕하세요' 같은 인사 생략. 바로 핵심으로 들어갈 것.
                2. 실전적 레퍼런스: '아이디어 수집' 같은 모호한 말 대신 "Product Hunt나 Indie Hackers에서 유사 사례 3개 분석"처럼 구체적인 툴/사이트 명시.
                3. 개발자적 사고: JDK 마이그레이션이나 PM 경험을 비즈니스 시스템(자동화)에 어떻게 녹일지 기술적 관점을 섞을 것.
                4. 첫 번째 액션(First Step): "지금 바로 [이 사이트]에 접속해서 [이것]을 검색하세요" 수준으로 구체화.
                5. 제약: 전체 500자 이내, 불필요한 미사여구(화이팅, 좋은 하루 등) 절대 금지."""
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
        hour=21,
        minute=0
    )
    scheduler.start()

    print("봇 실행 중...")
    app.run_polling()

if __name__ == "__main__":
    main()
