import asyncio
import signal
from multiprocessing import Process
from bot.bot import TelegramBot
from web.app import app
from config import Config

def run_web():
    app.run(host='0.0.0.0', port=5000)

class BotRunner:
    def __init__(self):
        self.bot = None
        self.web_process = None
        self.should_stop = False

    async def start_bot(self):
        self.bot = TelegramBot(Config.TELEGRAM_TOKEN)
        await self.bot.application.initialize()
        await self.bot.application.start()
        await self.bot.application.updater.start_polling()

        try:
            while not self.should_stop:
                await asyncio.sleep(1)
        finally:
            await self.cleanup()

    async def cleanup(self):
        if self.bot and self.bot.application:
            await self.bot.application.updater.stop()
            await self.bot.application.stop()
            await self.bot.application.shutdown()

        if self.web_process:
            self.web_process.terminate()
            self.web_process.join()

    def signal_handler(self):
        self.should_stop = True

def main():
    runner = BotRunner()

    # Set up signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda s, f: runner.signal_handler())

    # Start the Flask app in a separate process
    runner.web_process = Process(target=run_web)
    runner.web_process.start()

    # Run the Telegram bot with proper event loop handling
    try:
        asyncio.run(runner.start_bot())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()