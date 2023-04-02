import os
from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.environ.get("APP_NAME")
APP_SECRET = os.environ.get("APP_SECRET")
ADMIN_PSWD = os.environ.get("ADMIN_PSWD")

DB_FILE = os.environ.get("DB_FILE")
DB_URI = os.environ.get("DB_URI")

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")
