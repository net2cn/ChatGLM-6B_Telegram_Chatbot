import asyncio
import sys
import logging
from telegram import Update, Chat, Bot, User
from telegram.ext import filters, ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler

import torch
from transformers import AutoTokenizer, AutoModel

from config import GlobalConfig, CharacterConfig
from decorators import *

logging.basicConfig(format='[%(asctime)s] - %(message)s', level=logging.INFO)
tokenizer:AutoTokenizer
model:AutoModel

ENABLED_FLAG        = False
BOT: User           = None
prepend_history = []
history = {}

def load_character():
    logging.info(f"Loading character at: {GlobalConfig.config['character']}")
    try:
        CharacterConfig.load()
    except Exception as e:
        raise e

    global prepend_history
    #_, prepend_history = model.chat(tokenizer, character["char_persona"], history=[])
    prepend_history=[(CharacterConfig.character["char_persona"],"")]
    logging.info(f"Character loaded: {CharacterConfig.character}")
    logging.info(f"Prepend history: {prepend_history}")

def clear_history(chat_id=None):
    global history
    if chat_id!=None:
        history[chat_id] = []
    else:
        history={}

def update_history(chat_id, new_history):
    global history
    if len(new_history)>GlobalConfig.config["history_limit_per_session"]:
        history[chat_id]=new_history[-GlobalConfig.config["history_limit_per_session"]:]
    else:
        history[chat_id]=new_history[1:]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"User {update.message.chat.username} executed command: /{sys._getframe().f_code.co_name}")

    if update.effective_chat.id not in history:
        history[update.effective_chat.id]=[]
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to ChatGLM-6b Telegram bot. Send in any message to start chatting.")

@trusted_user
@log_command
async def enable(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ENABLED_FLAG
    if ENABLED_FLAG:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="This bot is already running.")
        return

    ENABLED_FLAG=True

    clear_history()
    load_character()

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Enabled. Happy chatting~")

@trusted_user
@log_command
async def disable(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ENABLED_FLAG
    if not ENABLED_FLAG:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="This bot is already stopped.")
        return

    ENABLED_FLAG=False

    clear_history()

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Bye!")

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"User {update.message.chat.username} executed command: /{sys._getframe().f_code.co_name}")
    
    global ENABLED_FLAG
    if not ENABLED_FLAG:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="This bot is disabled. Use /start to enable it.")
        return
    
    if context.args and context.args[0]=="all" and update.effective_user.id in GlobalConfig.config["trusted_id"]:
        clear_history()
        await context.bot.send_message(chat_id=update.effective_chat.id, text="All session chat history cleared.")
    else:
        clear_history(update.effective_chat.id)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Current session chat history cleared.")

@trusted_user
@log_command
async def reload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"User {update.message.chat.username} executed command: /{sys._getframe().f_code.co_name}")
    
    global ENABLED_FLAG
    if not ENABLED_FLAG:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="This bot is disabled. Use /start to enable it.")
        return
    
    clear_history(update.effective_chat.id)
    load_character()

    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Character reloaded: {CharacterConfig.character}\nPrepend history: {prepend_history}")

@log_command
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info(f"User {update.message.chat.username} executed command: /{sys._getframe().f_code.co_name}")

    global ENABLED_FLAG
    global history
    chat_id = update.effective_chat.id
    cuda_memory = torch.cuda.mem_get_info()
    if chat_id not in history:
        history[chat_id]=[]

    resp = "-== Chatbot Statistics ==-\n"
    resp += f"Enabled: {ENABLED_FLAG}\n"
    resp += f"Seesion: {len(history)} session(s)\n"
    resp += f"Prepend history: {len(prepend_history)} item(s)\n"
    resp += f"Current session history: {len(history[chat_id])} item(s)\n"
    resp += f"Effective session history: {len(prepend_history)+len(history[chat_id])} item(s)\n"
    resp += f"All session history: {len(prepend_history)+sum(len(his) for his in history.values())} item(s)\n"
    resp += "-== Hardware Statistics ==-\n"
    resp += f"GPU: {torch.cuda.get_device_name()}\n"
    resp += f"VRAM: {(cuda_memory[1]-cuda_memory[0])/1024/1024}MB/{cuda_memory[1]/1024/1024}MB"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=resp)

@log_command
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raise NotImplementedError

async def process_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = chat_id=update.effective_chat.id
    username = update.message.from_user.username
    user_id = update.message.from_user.id
    request=""

    global ENABLED_FLAG
    if not ENABLED_FLAG:
        await context.bot.send_message(chat_id=chat_id, text="This bot is disabled. Use /start to enable it.")
        return
    
    if (update.message.chat.type == Chat.PRIVATE and user_id not in GlobalConfig.config["trusted_id"]):
        await context.bot.send_message(chat_id=chat_id, text="This bot is not functional to unauthorized personnel.")
        return
    
    if (context.args):
        request=" ".join(context.args)
    else:
        request = update.message.text
    request = request.strip()
    logging.info(f"{username} ({user_id}, {chat_id}): {request}")
    if (request.startswith(BOT.name)):
        request = request[len(BOT.name)+1:]
    
    if len(request)>GlobalConfig.config["request_length_limit"]:
        logging.info("Request too long, will not respond.")
        await context.bot.send_message(chat_id=chat_id, text=f"Your given input exceeded maximum allowed length {GlobalConfig.config['request_length_limit']}. Will not respond.")
        return

    global history
    global prepend_history
    request = CharacterConfig.character["formatter"].format(user=username, input=request)
    new_history=[]
    if update.effective_chat.id not in history:
        history[update.effective_chat.id]=[]
    try:
        response, new_history = model.chat(tokenizer, request, history=[*prepend_history, *history[update.effective_chat.id]])
    except Exception as e:
        logging.exception("An exception has occurred during chatting.")
        logging.exception(e)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"An exception has occurred: {type(e).__name__}")
        return
    update_history(update.message.chat_id, new_history)

    logging.info(f"AI: {response}")

    await context.bot.send_message(chat_id=update.effective_chat.id, text=response)

if __name__ == "__main__":
    logging.info("Bringing up telegram bot...")

    if not GlobalConfig.config["telegram_api_key"]:
        logging.error("Telegram bot api key is not set in config file. Exitting...")
        exit()

    application = ApplicationBuilder().token(GlobalConfig.config["telegram_api_key"]).build()
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    enable_handler = CommandHandler('enable', enable)
    application.add_handler(enable_handler)

    disable_handler = CommandHandler('disable', disable)
    application.add_handler(disable_handler)

    clear_handler = CommandHandler('clear', clear)
    application.add_handler(clear_handler)

    reload_handler = CommandHandler('reload', reload)
    application.add_handler(reload_handler)

    stats_handler = CommandHandler('stats', stats)
    application.add_handler(stats_handler)

    chat_handler = CommandHandler('chat', process_user_message)
    application.add_handler(chat_handler)

    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), process_user_message)
    application.add_handler(message_handler)

    loop=asyncio.get_event_loop()
    BOT = loop.run_until_complete(application.bot.get_me())
    if BOT==None:
        logging.error("Unable to execute get_me() to obtain bot info. Exitting...")
        exit()

    load_character()

    logging.info("Loading models...")
    tokenizer = AutoTokenizer.from_pretrained("THUDM/chatglm-6b-int4", trust_remote_code=True)
    model = AutoModel.from_pretrained("THUDM/chatglm-6b-int4", trust_remote_code=True, proxies={"http":"http://localhost:8080", "https": "http://localhost:8080"}).half().cuda()
    model = model.eval()

    application.run_polling()