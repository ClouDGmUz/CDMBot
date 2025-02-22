from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
import asyncio
import re
from database.db import Database

class TelegramBot:
    def __init__(self, token):
        self.application = Application.builder().token(token).build()
        self.setup_handlers()
        self.db = Database()

    def setup_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("addbadword", self.add_bad_word))
        self.application.add_handler(CommandHandler("removebadword", self.remove_bad_word))
        self.application.add_handler(CommandHandler("listbadwords", self.list_bad_words))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.echo))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text('Hello! I am your bot.')

    async def is_admin(self, chat_id: int, user_id: int) -> bool:
        try:
            chat_member = await self.application.bot.get_chat_member(chat_id, user_id)
            is_admin = chat_member.status in ['administrator', 'creator']
            self.db.add_or_update_user(user_id, chat_member.user.username, is_admin)
            return is_admin
        except Exception:
            return False

    def contains_link(self, text: str) -> bool:
        url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            r'|(?:www\.)[a-zA-Z0-9\-.]+\.[a-zA-Z]{2,}(?:/[^\s]*)?'
            r'|(?:[a-zA-Z0-9\-.]+\.(?:com|org|net|edu|gov|mil|biz|info|io|uk|de|ru|jp|cn|br|in|fr|it|nl|eu|me|tv))(?:/[^\s]*)?'
        )
        return bool(url_pattern.search(text))

    async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text:
            return

        # Check if message is from a group
        if update.message.chat.type in ['group', 'supergroup']:
            is_admin = await self.is_admin(update.message.chat_id, update.message.from_user.id)
            
            # If message contains link and sender is not admin
            if self.contains_link(update.message.text) and not is_admin:
                try:
                    # Log the attempt before taking action
                    self.db.log_link_attempt(
                        user_id=update.message.from_user.id,
                        chat_id=update.message.chat_id,
                        link_text=update.message.text,
                        action_taken='deleted'
                    )
                    
                    # Delete the message
                    await update.message.delete()
                    
                    # Get number of attempts in last 24 hours
                    attempts = self.db.get_user_attempts(
                        user_id=update.message.from_user.id,
                        chat_id=update.message.chat_id
                    )
                    
                    # Send warning with attempt count
                    warning_msg = f"@{update.message.from_user.username or update.message.from_user.id}, sending links is not allowed in this group! This is your {attempts} attempt in 24 hours."
                    await context.bot.send_message(
                        chat_id=update.message.chat_id,
                        text=warning_msg
                    )
                except Exception as e:
                    print(f"Error in link moderation: {str(e)}")
                return

            # Check for bad words if sender is not admin
            if not is_admin:
                bad_words = [word['word'] for word in self.db.get_bad_words()]
                message_lower = update.message.text.lower()
                for bad_word in bad_words:
                    if bad_word in message_lower:
                        try:
                            # Log the attempt before taking action
                            self.db.log_bad_word_attempt(
                                user_id=update.message.from_user.id,
                                chat_id=update.message.chat_id,
                                message_text=update.message.text,
                                matched_word=bad_word,
                                action_taken='deleted'
                            )
                            
                            # Delete the message
                            await update.message.delete()
                            
                            # Get number of attempts in last 24 hours
                            attempts = self.db.get_user_attempts(
                                user_id=update.message.from_user.id,
                                chat_id=update.message.chat_id
                            )
                            
                            # Send warning with attempt count
                            warning_msg = f"@{update.message.from_user.username or update.message.from_user.id}, using bad words is not allowed in this group! This is your {attempts} attempt in 24 hours."
                            await context.bot.send_message(
                                chat_id=update.message.chat_id,
                                text=warning_msg
                            )
                            return
                        except Exception as e:
                            print(f"Error in bad word moderation: {str(e)}")
                            return

        # If no violations or user is admin, echo the message
        await update.message.reply_text(update.message.text)

    async def add_bad_word(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Please provide a word to add.")
            return

        is_admin = await self.is_admin(update.message.chat_id, update.message.from_user.id)
        if not is_admin:
            await update.message.reply_text("Only admins can add bad words.")
            return

        word = context.args[0].lower()
        self.db.add_bad_word(word, update.message.from_user.id)
        await update.message.reply_text(f"Added '{word}' to bad words list.")

    async def remove_bad_word(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Please provide a word to remove.")
            return

        is_admin = await self.is_admin(update.message.chat_id, update.message.from_user.id)
        if not is_admin:
            await update.message.reply_text("Only admins can remove bad words.")
            return

        word = context.args[0].lower()
        self.db.remove_bad_word(word)
        await update.message.reply_text(f"Removed '{word}' from bad words list.")

    async def list_bad_words(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        is_admin = await self.is_admin(update.message.chat_id, update.message.from_user.id)
        if not is_admin:
            await update.message.reply_text("Only admins can view bad words list.")
            return

        bad_words = self.db.get_bad_words()
        if not bad_words:
            await update.message.reply_text("No bad words in the list.")
            return

        words_list = "\n".join([f"- {word}" for word in bad_words])
        await update.message.reply_text(f"Current bad words list:\n{words_list}")

    def run(self):
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # Run the bot using the event loop - simplified to avoid duplicate initialization
        loop.run_until_complete(self.application.run_polling())
        loop.close()