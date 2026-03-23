import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot
from telegram.ext import Application, MessageHandler, filters
from apscheduler.schedulers.background import BackgroundScheduler
from openai import OpenAI
from tavily import TavilyClient
from pytz import timezone

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
MY_CHAT_ID = os.getenv("MY_CHAT_ID")

openai_client = OpenAI(api_key=OPENAI_API_KEY)
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

INTERESTS = "SaaS 빌딩을 통한 수익 얻기 - 실제 수익 사례, 첫 고객 확보 전략, 가격 책정, 마케팅 채널"

async def handle_message(update, context):
    text = update.message.text
    chat_id = str(update.message.chat_id)
    print(f"Chat ID: {chat_id}")
    await update.message.reply_text(f"✅ 메시지 수신: {text}")

def send_morning_briefing():
    asyncio.run(_send_morning_briefing())

def send_afternoon_check():
    asyncio.run(_send_afternoon_check())

def send_evening_check():
    asyncio.run(_send_evening_check())

async def _send_morning_briefing():
    bot = Bot(token=TELEGRAM_TOKEN)

    # Tavily로 최신 정보 검색
    search_result = tavily_client.search(
        query="SaaS revenue growth first customer acquisition 2025",
        search_depth="advanced",
        max_results=3
    )

    search_content = "\n".join([
        f"- {r['title']}: {r['content'][:200]}"
        for r in search_result['results']
    ])

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """당신은 6년 차 SI/SM 개발자이자 팀 리드인 사용자의 '비즈니스 가속화 코치'입니다.
사용자는 SaaS 빌딩을 통한 수익화에 집중하고 있습니다.

[규칙]
1. 인사 생략. 바로 핵심으로.
2. 모호한 표현 금지. 구체적인 툴/사이트 명시.
3. 오늘 바로 실행 가능한 action item 2개 포함.
4. 미사여구 절대 금지.
5. 전체 500자 이내."""
            },
            {
                "role": "user",
                "content": f"""관심사: {INTERESTS}

최신 검색 결과:
{search_content}

위 정보를 바탕으로 오늘의 아침 브리핑을 작성해주세요.
형식:
📌 핵심 인사이트 (2~3줄)
⚡ 오늘 action item 2개 (구체적인 첫 번째 실행 포함)"""
            }
        ]
    )

    message = f"🌅 모닝 브리핑\n\n{response.choices[0].message.content}"
    await bot.send_message(chat_id=MY_CHAT_ID, text=message)

async def _send_afternoon_check():
    bot = Bot(token=TELEGRAM_TOKEN)
    message = "⚡ 오늘 아침 action item 진행 중인가요?\n\n완료했으면 ✅, 못했으면 ❌ 로 답장해주세요."
    await bot.send_message(chat_id=MY_CHAT_ID, text=message)

async def _send_evening_check():
    bot = Bot(token=TELEGRAM_TOKEN)
    message = "🌙 오늘 하루 마무리\n\n오늘 action item 완료했나요? 내일 브리핑에 반영할 내용 있으면 지금 입력해주세요."
    await bot.send_message(chat_id=MY_CHAT_ID, text=message)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    kst = timezone('Asia/Seoul')
    scheduler = BackgroundScheduler(timezone=kst)

    # 아침 브리핑
    scheduler.add_job(send_morning_briefing, 'cron', hour=6, minute=0)
    # 오후 체크
    scheduler.add_job(send_afternoon_check, 'cron', hour=12, minute=0)
    # 저녁 체크
    scheduler.add_job(send_evening_check, 'cron', hour=21, minute=0)

    scheduler.start()

    print("봇 실행 중...")
    app.run_polling()

if __name__ == "__main__":
    asyncio.run(_send_morning_briefing())