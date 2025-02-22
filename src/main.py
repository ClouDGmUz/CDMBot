import asyncio
from multiprocessing import Process
from bot.bot import TelegramBot
from web.app import app
from config import Config

def run_web():
    app.run(host='0.0.0.0', port=5000)

async def run_bot():
    bot = TelegramBot(Config.TELEGRAM_TOKEN)
    await bot.application.run_polling()

def main():
    # Start the Flask app in a separate process
    web_process = Process(target=run_web)
    web_process.start()

    # Run the Telegram bot in the main process
    asyncio.run(run_bot())

if __name__ == "__main__":
    main()