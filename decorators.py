import logging

from typing_extensions import Unpack, TypedDict
from config import GlobalConfig

from telegram import Update
from telegram.ext import ContextTypes

# permissions
# all user can call
def all(handler):
    async def wrapper(update:Update, context:ContextTypes.DEFAULT_TYPE):
        return await handler(update, context)
    return wrapper

# only trusted user can call
def trusted_user(handler):
    async def wrapper(update:Update, context:ContextTypes.DEFAULT_TYPE):
        user_id=update.effective_user.id
        chat_id=update.effective_chat.id
        if user_id not in GlobalConfig.config['trusted_id']:
            await context.bot.send_message(chat_id=chat_id, text="You are not allowed to execute this command.")
            return
        return await handler(update, context)
    return wrapper

# helpers
def log_command(handler):
    async def wrapper(update:Update, context:ContextTypes.DEFAULT_TYPE):
        logging.info(f"User {update.message.chat.username} executed command: /{handler.__name__}")
        return await handler(update, context)
    return wrapper