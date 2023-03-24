import os
import json
import logging
from typing_extensions import TypedDict

from . import GlobalConfig

class Character(TypedDict):
    char_name: str
    char_persona: str
    formatter: str

character = Character(json.load(open(GlobalConfig.config['character'], "r")))

def load(path: str=GlobalConfig.config['character']):
    if not os.path.exists(path):
        logging.warn(f"Unable to locate config file at {path}.")
        return

    with open(path, "r", encoding="utf8") as f:
        data = json.load(f)
        global character
        character=Character(data)
load()