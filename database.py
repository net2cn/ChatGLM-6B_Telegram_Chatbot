from peewee import *
import datetime

from config import GlobalConfig

db = SqliteDatabase(GlobalConfig.DEFAULT_DATABSE_PATH)

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    user_id = IntegerField(unique=True, index=True)
    permissions = TextField()

def check_permission(user_id:int, permission:str)->bool:
    user:User = User.get(user_id=user_id)
    if permission not in user.permissions:
        return True
    return False

def add_permission(user_id:int, permission:str):
    user:User=User.get(user_id=user_id)
    if user==None:
        user=User.create(user_id=user_id, permission="")
    if permission not in user.permissions:
        user.permissions=f"{user.permissions},{permission}"
    user.save()

db.connect()
db.create_tables([User])