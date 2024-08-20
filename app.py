from flask import Flask, request
import os
import logging
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from datetime import datetime, timedelta

app = Flask(__name__)

# Initialize your bot with the token from the environment variable
TOKEN = os.getenv('TOKEN')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
bot = Bot(token=TOKEN)

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Initialize the dispatcher
dispatcher = Dispatcher(bot, update_queue=None, workers=0, use_context=True)

# Dictionary to store the last message time for each user
last_message_time = {}

# Set to store banned users' chat IDs
banned_users = set()

# Define the /start command handler
def start(update, context):
    if update.effective_chat.id in banned_users:
        context.bot.send_message(chat_id=update.effective_chat.id, text="You are banned from using this bot.")
        return
    context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to the Livegram Bot! 😊\n\nThis bot allows you to send messages directly to the admin. Feel free to ask any questions or share your thoughts. An admin will get back to you shortly!")

# Define the /ban command handler
def ban(update, context):
    if update.effective_chat.id == int(ADMIN_CHAT_ID):
        if update.message.reply_to_message:
            banned_user_id = update.message.reply_to_message.forward_from.id
            banned_users.add(banned_user_id)
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"User {banned_user_id} has been banned.")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Please reply to the user's message to ban them.")

# Define the /unban command handler
def unban(update, context):
    if update.effective_chat.id == int(ADMIN_CHAT_ID):
        if update.message.reply_to_message:
            unbanned_user_id = update.message.reply_to_message.forward_from.id
            banned_users.discard(unbanned_user_id)
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"User {unbanned_user_id} has been unbanned.")
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Please reply to the user's message to unban them.")

# Define a message handler for forwarding messages, files, images, and videos to the admin
def handle_message(update, context):
    chat_id = update.effective_chat.id

    # Check if the user is banned
    if chat_id in banned_users:
        context.bot.send_message(chat_id=chat_id, text="You are banned from using this bot.")
        return

    now = datetime.now()

    # Check if the user has sent a message within the last 15 minutes
    if chat_id in last_message_time:
        time_diff = now - last_message_time[chat_id]
        if time_diff < timedelta(minutes=15):
            forward_message(update, context, chat_id)
            return

    # Update the last message time for the user
    last_message_time[chat_id] = now

    # Forward the message and send a confirmation message
    forward_message(update, context, chat_id)
    context.bot.send_message(chat_id=chat_id, text="Your message has been forwarded to the admin.")

def forward_message(update, context, chat_id):
    # If the message is from the admin, reply to the original sender
    if chat_id == int(ADMIN_CHAT_ID):
        if update.message.reply_to_message:  # Ensure the admin is replying to a forwarded message
            original_message_id = update.message.reply_to_message.message_id
            original_data = context.bot_data.get(original_message_id)
            if original_data:
                target_chat_id = original_data['chat_id']
                if update.message.text:
                    context.bot.send_message(chat_id=target_chat_id, text=update.message.text)
                elif update.message.photo:
                    context.bot.send_photo(chat_id=target_chat_id, photo=update.message.photo[-1].file_id, caption=update.message.caption)
                elif update.message.video:
                    context.bot.send_video(chat_id=target_chat_id, video=update.message.video.file_id, caption=update.message.caption)
                elif update.message.document:
                    context.bot.send_document(chat_id=target_chat_id, document=update.message.document.file_id, caption=update.message.caption)
                elif update.message.audio:
                    context.bot.send_audio(chat_id=target_chat_id, audio=update.message.audio.file_id, caption=update.message.caption)
                elif update.message.voice:
                    context.bot.send_voice(chat_id=target_chat_id, voice=update.message.voice.file_id, caption=update.message.caption)
                elif update.message.sticker:
                    context.bot.send_sticker(chat_id=target_chat_id, sticker=update.message.sticker.file_id)
                else:
                    context.bot.send_message(chat_id=target_chat_id, text="Received an unsupported message type.")
            else:
                context.bot.send_message(chat_id=ADMIN_CHAT_ID, text="Error: Original message not found.")
        else:
            context.bot.send_message(chat_id=ADMIN_CHAT_ID, text="Please reply to a forwarded message to respond to the user.")
    else:
        # Forward different types of messages to the admin without reply markup
        if update.message.text:
            forwarded_message = context.bot.forward_message(chat_id=ADMIN_CHAT_ID, from_chat_id=chat_id, message_id=update.message.message_id)
        elif update.message.photo:
            forwarded_message = context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=update.message.photo[-1].file_id, caption=update.message.caption)
        elif update.message.video:
            forwarded_message = context.bot.send_video(chat_id=ADMIN_CHAT_ID, video=update.message.video.file_id, caption=update.message.caption)
        elif update.message.document:
            forwarded_message = context.bot.send_document(chat_id=ADMIN_CHAT_ID, document=update.message.document.file_id, caption=update.message.caption)
        elif update.message.audio:
            forwarded_message = context.bot.send_audio(chat_id=ADMIN_CHAT_ID, audio=update.message.audio.file_id, caption=update.message.caption)
        elif update.message.voice:
            forwarded_message = context.bot.send_voice(chat_id=ADMIN_CHAT_ID, voice=update.message.voice.file_id, caption=update.message.caption)
        elif update.message.sticker:
            forwarded_message = context.bot.send_sticker(chat_id=ADMIN_CHAT_ID, sticker=update.message.sticker.file_id)
        else:
            context.bot.send_message(chat_id=ADMIN_CHAT_ID, text="Received an unsupported message type.")

        # Store the original chat_id and message_id to reply back later, but no reply markup
        context.bot_data[forwarded_message.message_id] = {'chat_id': chat_id, 'message_id': update.message.message_id}

# Register handlers
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('ban', ban))
dispatcher.add_handler(CommandHandler('unban', unban))
dispatcher.add_handler(MessageHandler(Filters.all & ~Filters.command, handle_message))

# Define the webhook route
@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
