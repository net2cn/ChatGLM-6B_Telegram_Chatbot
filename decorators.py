import logging

from typing import Callable
from typing_extensions import Unpack, TypedDict


from telegram import Update
from telegram.ext import ContextTypes

from config import GlobalConfig
import database


# permissions
def require_permission(permission:str):
    def decorator(handler:Callable):
        async def wrapper(update:Update, context:ContextTypes.DEFAULT_TYPE):
            user_id=update.effective_user.id
            chat_id=update.effective_chat.id
            if user_id in GlobalConfig.config['trusted_id'] or database.check_permission(user_id, permission):
                return await handler(update, context)
            await context.bot.send_message(chat_id=chat_id, text="You are not allowed to execute this command.")
        return wrapper
    return decorator

# helpers
def log_command(handler:Callable):
    async def wrapper(update:Update, context:ContextTypes.DEFAULT_TYPE):
        logging.info(f"User {update.message.chat.username} executed command: /{handler.__name__}")
        return await handler(update, context)
    return wrapper