from flask import Flask, request
import os
import logging
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters

app = Flask(__name__)

# Initialize your bot with the token from the environment variable
TOKEN = os.getenv('TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
bot = Bot(token=TOKEN)

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Initialize the dispatcher
dispatcher = Dispatcher(bot, update_queue=None, workers=0, use_context=True)

# Define the /start command handler
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to the Livegram Bot! 😊\n\nThis bot allows you to send messages directly to the admin. Feel free to ask any questions or share your thoughts. An admin will get back to you shortly!")

# Define a message handler for forwarding messages to the admin
def handle_message(update, context):
    if update.effective_chat.id == int(ADMIN_CHAT_ID):
        original_message_id = update.message.reply_to_message.message_id
        original_data = context.bot_data.get(original_message_id)
        if original_data:
            context.bot.send_message(chat_id=original_data['chat_id'], text=update.message.text, reply_to_message_id=original_data['message_id'])
        else:
            context.bot.send_message(chat_id=ADMIN_CHAT_ID, text="Error: Original message not found.")
    else:
        forwarded_message = context.bot.forward_message(chat_id=ADMIN_CHAT_ID, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)
        context.bot_data[forwarded_message.message_id] = {'chat_id': update.effective_chat.id, 'message_id': update.message.message_id}
        context.bot.send_message(chat_id=update.effective_chat.id, text="Your message has been forwarded to the admin.")

# Register handlers
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

# Define the webhook route
@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
