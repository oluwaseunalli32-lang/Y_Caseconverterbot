import os
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Storage for the user's last message text (Simple memory cache)
user_data_store = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"👋 Hi {user.mention_html()}!\n\n"
        "Welcome to <b>Y_Caseconverterbot</b>. Send me any text, and I will help you format it instantly!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Store the text and present case options to the user."""
    text = update.message.text
    user_id = update.effective_user.id
    user_data_store[user_id] = text  # Save text

    # Define the inline keyboard layout
    keyboard = [
        [
            InlineKeyboardButton("UPPERCASE", callback_data='upper'),
            InlineKeyboardButton("lowercase", callback_data='lower')
        ],
        [
            InlineKeyboardButton("Title Case", callback_data='title'),
            InlineKeyboardButton("Sentence case", callback_data='sentence')
        ],
        [
            InlineKeyboardButton("iNVERT cASE", callback_data='invert')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose the target text format:", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button presses and edit the message with converted text."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    original_text = user_data_store.get(user_id)

    if not original_text:
        await query.edit_message_text("Error: Text expired or not found. Please send your text again.")
        return

    action = query.data

    if action == 'upper':
        converted = original_text.upper()
    elif action == 'lower':
        converted = original_text.lower()
    elif action == 'title':
        converted = original_text.title()
    elif action == 'sentence':
        converted = original_text.capitalize()
    elif action == 'invert':
        converted = original_text.swapcase()
    else:
        converted = original_text

    # Wrap in code block for easy one-tap copying in Telegram
    formatted_text = f"```{converted}```"
    
    await query.edit_message_text(text=formatted_text, parse_mode="MarkdownV2")

@app.route('/' + os.getenv('TOKEN', 'telegram-token'), methods=['POST'])
def webhook():
    """Receive updates from Telegram and feed them into the application."""
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), telegram_app.bot)
        telegram_app.create_task(telegram_app.process_update(update))
    return 'ok', 200

@app.route('/')
def index():
    return "Bot is running!", 200

# Global setup block for production/Gunicorn environments
token = os.getenv("TOKEN")
url = os.getenv("RENDER_EXTERNAL_URL")

if not token or not url:
    logger.warning("Environment variables TOKEN or RENDER_EXTERNAL_URL are missing!")

# Build the Telegram Application
telegram_app = Application.builder().token(token).updater(None).build()

# Add handlers
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
telegram_app.add_handler(CallbackQueryHandler(button_click))

# Initialize the app background tasks and establish webhook
telegram_app.initialize()
telegram_app.start()
if url and token:
    telegram_app.bot.set_webhook(url=f"{url}/{token}")

if __name__ == '__main__':
    # This block only executes if you run 'python bot.py' directly locally
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
