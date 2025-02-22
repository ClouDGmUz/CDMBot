import threading
from bot.bot import TelegramBot
from web.app import app
from config import Config

def run_bot():
    bot = TelegramBot(Config.TELEGRAM_TOKEN)
    bot.run()

def run_web():
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    # Run Flask app in main thread
    run_web()