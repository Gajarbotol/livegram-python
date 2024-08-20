from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters, CommandHandler
import os

app = Flask(__name__)

TOKEN = os.getenv('TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, use_context=True)

# Dictionary to store messages for replies
messages = {}

@app.route('/')
def home():
    return "Bot is running!"

@app.route(f'/webhook/{TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200

# Handler for the /start command
def start(update, context):
    welcome_message = (
        "Welcome to the Livegram Bot! 😊\n\n"
        "This bot allows you to send messages directly to the admin. "
        "Feel free to ask any questions or share your thoughts. An admin will get back to you shortly!"
    )
    context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_message)

# Handler for regular messages
def handle_message(update, context):
    chat_id = update.effective_chat.id
    message_id = update.message.message_id

    if str(chat_id) == ADMIN_CHAT_ID:
        original_message_id = update.message.reply_to_message.message_id
        original_data = messages.get(original_message_id)

        if original_data:
            context.bot.send_message(
                chat_id=original_data['chat_id'],
                text=update.message.text,
                reply_to_message_id=original_data['message_id']
            )
        else:
            context.bot.send_message(chat_id=ADMIN_CHAT_ID, text="Error: Original message not found.")
    else:
        forwarded_message = context.bot.forward_message(
            chat_id=ADMIN_CHAT_ID,
            from_chat_id=chat_id,
            message_id=message_id
        )
        messages[forwarded_message.message_id] = {'chat_id': chat_id, 'message_id': message_id}
        context.bot.send_message(chat_id=chat_id, text="Your message has been forwarded to the admin.")

# Register handlers
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

if __name__ == '__main__':
    app.run(port=3000)
