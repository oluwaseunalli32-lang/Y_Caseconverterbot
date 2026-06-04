import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Temporary user text memory
user_data_store = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"👋 Hi {user.mention_html()}!\n\n"
        "Welcome to <b>Y_Caseconverterbot</b>. Send me any text, and I will help you format it instantly!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Store text and present options."""
    text = update.message.text
    user_id = update.effective_user.id
    user_data_store[user_id] = text

    keyboard = [
        [InlineKeyboardButton("UPPERCASE", callback_data='upper'),
         InlineKeyboardButton("lowercase", callback_data='lower')],
        [InlineKeyboardButton("Title Case", callback_data='title'),
         InlineKeyboardButton("Sentence case", callback_data='sentence')],
        [InlineKeyboardButton("iNVERT cASE", callback_data='invert')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose the target text format:", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle layout selection."""
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

    # Fixed syntax formatting for Markdown code block strings
    await query.edit_message_text(text=f'```{converted}```', parse_mode="MarkdownV2")

def main():
    token = os.getenv("TOKEN")
    url = os.getenv("RENDER_EXTERNAL_URL")
    port = int(os.getenv("PORT", 8000))

    if not token or not url:
        logger.error("Missing configuration: Ensure TOKEN and RENDER_EXTERNAL_URL are set!")
        return

    # Build the native async application
    application = Application.builder().token(token).build()

    # Register Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_click))

    # Start the native webhook handler that perfectly aligns with Render's environment
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=token,
        webhook_url=f"{url}/{token}"
    )

if __name__ == '__main__':
    main()
