import json
import os
import logging
from typing_extensions import TypedDict

DEFAULT_CONFIG_PATH = "./config.json"

class Config(TypedDict):
    enabled: bool
    trusted_id: set
    character: str
    telegram_api_key: str
    request_length_limit: int
    history_limit_per_session: int

config = Config(enabled=False,
                trusted_id=set(),
                character="./characters/default.json",
                telegram_api_key="[YOUR_TELEGRAM_API_KEY]",
                request_length_limit=100,
                history_limit_per_session=5,
                )

def serialize_set(obj:object):
    if isinstance(obj, set):
        return list(obj)
    return obj

def save(path: str=DEFAULT_CONFIG_PATH):
    with open(path, "w", encoding="utf8") as f:
        global config
        json.dump(config, f, indent=4, default=serialize_set)

def load(path: str = DEFAULT_CONFIG_PATH):
    if not os.path.exists(path):
        logging.warn(f"Unable to locate config file at {path}. Generating new config file at given path...")
        save(path)

    with open(path, "r", encoding="utf8") as f:
        data = json.load(f)
        data["trusted_id"]=set(data["trusted_id"])
        global config
        config=Config(data)

load()