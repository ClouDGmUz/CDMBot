import asyncio
from bot.bot import TelegramBot
from web.app import app
from config import Config
from aioflask import Flask

async def run_bot():
    bot = TelegramBot(Config.TELEGRAM_TOKEN)
    await bot.application.run_polling()

async def run_web():
    app.run_task(host='0.0.0.0', port=5000)

async def main():
    await asyncio.gather(
        run_bot(),
        run_web()
    )

if __name__ == "__main__":
    asyncio.run(main())