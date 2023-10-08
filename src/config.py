import os
from dotenv import load_dotenv

load_dotenv()

CRM_NAME = os.environ.get("CRM_NAME")
APP_DOMAIN = os.environ.get("APP_DOMAIN")
APP_TYPE = os.environ.get("APP_TYPE")
APP_SECRET = os.environ.get("APP_SECRET")
ADMIN_PSWD = os.environ.get("ADMIN_PSWD")

DB_FILE = os.environ.get("DB_FILE")
DB_URI = os.environ.get("DB_URI")

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

SENTRY_TOKEN = os.environ.get("SENTRY_TOKEN")
SENTRY_RATE = os.environ.get("SENTRY_RATE")

PLATFORM_INTEGRATION_IS_ON = os.environ.get("PLATFORM_INTEGRATION_IS_ON")
