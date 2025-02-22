# CDMBot - Chat Moderation Bot

CDMBot is a Telegram bot designed to help moderate group chats by filtering out unwanted links and bad words. It comes with a web-based admin interface for easy management of moderation settings.

## Features

### Telegram Bot
- Automatic link filtering for non-admin users
- Bad word detection and message removal
- Attempt tracking and warning messages
- Admin-only commands for moderation
- Interactive responses to general messages

### Web Admin Interface
- Dashboard for monitoring bot activity
- Bad words management
- Blocked links management
- Secure login system

## Setup Instructions

1. Clone the repository
2. Create a `.env` file with the following variables:
   ```
   TELEGRAM_TOKEN=your_bot_token
   WEBHOOK_URL=http://localhost:5000
   ADMIN_USERNAME=your_admin_username
   ADMIN_PASSWORD=your_admin_password
   SECRET_KEY=your_secret_key
   ```
3. Install dependencies:
   ```bash
   pip install python-telegram-bot python-dotenv flask
   ```
4. Run the application:
   ```bash
   python src/main.py
   ```

## Bot Commands

- `/start` - Initialize the bot
- `/addbadword [word]` - Add a word to the bad words list (admin only)
- `/removebadword [word]` - Remove a word from the bad words list (admin only)
- `/listbadwords` - View the current list of bad words (admin only)

## Web Interface

Access the admin interface at `http://localhost:5000` with your configured admin credentials.

### Features:
- Dashboard: Overview of bot activity
- Bad Words: Manage filtered words
- Blocked Links: View and manage blocked link attempts

## Security

- Admin-only access to moderation commands
- Secure web interface with login system
- Link and bad word filtering for non-admin users
- Attempt tracking and user management

## Contributing

Contributions are welcome! Please feel free to submit pull requests.

## License

This project is licensed under the MIT License.