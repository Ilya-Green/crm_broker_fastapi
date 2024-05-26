import os
from dotenv import load_dotenv

load_dotenv()

CRM_NAME = os.environ.get("CRM_NAME")
APP_DOMAIN = os.environ.get("APP_DOMAIN")
APP_TYPE = os.environ.get("APP_TYPE")
APP_SECRET = os.environ.get("APP_SECRET")
ADMIN_PSWD = os.environ.get("ADMIN_PSWD")

CRM_TIMEZONE = os.environ.get("CRM_TIMEZONE")

DB_URI = os.environ.get("DB_URI")
DB_FILE = os.environ.get("DB_FILE")

TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

SENTRY_TOKEN = os.environ.get("SENTRY_TOKEN")
SENTRY_RATE = os.environ.get("SENTRY_RATE")

PLATFORM_INTEGRATION_IS_ON = os.environ.get("PLATFORM_INTEGRATION_IS")
if PLATFORM_INTEGRATION_IS_ON == "1":
    PLATFORM_INTEGRATION_IS_ON = True
else:
    PLATFORM_INTEGRATION_IS_ON = False
PLATFORM_INTEGRATION_URL = os.environ.get("PLATFORM_INTEGRATION_URL")
PLATFORM_INTEGRATION_SYNC = os.environ.get("PLATFORM_INTEGRATION_SYNC")
if PLATFORM_INTEGRATION_SYNC == "1":
    PLATFORM_INTEGRATION_SYNC = True
else:
    PLATFORM_INTEGRATION_SYNC = False
