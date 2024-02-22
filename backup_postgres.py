import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
import sys
import requests

sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
APP_DOMAIN = os.getenv("APP_DOMAIN")
APP_TYPE = os.getenv("APP_TYPE")
TG_TOKEN = os.getenv("TG_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")


BACKUP_DIR = os.getenv("BACKUP_DIR", "backup")
TIMESTAMP = datetime.now().strftime("%Y%m%d%H%M%S")
BACKUP_FILE = f"{BACKUP_DIR}/backup_{TIMESTAMP}.sql"

os.makedirs(BACKUP_DIR, exist_ok=True)

backup_command = f"pg_dump -h {DB_HOST} -p {DB_PORT} -U {DB_USER} -d {DB_NAME} -F c -b -v > {BACKUP_FILE}"

try:
    subprocess.run(backup_command, shell=True, check=True, env={"PGPASSWORD": DB_PASSWORD})
    print(f"Резервное копирование успешно создано: {BACKUP_FILE}")

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage?chat_id={TG_CHAT_ID}&text={APP_DOMAIN} : {APP_TYPE} : Резервное копирование успешно создано: {BACKUP_FILE}&disable_notification=true"
    print(requests.get(url).json())

    send_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument?chat_id={TG_CHAT_ID}"
    with open(BACKUP_FILE, "rb") as file:
        response = requests.post(send_url, files={"document": file})
    if response.ok:
        print("Файл успешно отправлен в Telegram")
    else:
        print(f"Ошибка при отправке файла в Telegram: {response.text}")

except subprocess.CalledProcessError as e:
    print(f"Ошибка при создании резервной копии: {e}")

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage?chat_id={TG_CHAT_ID}&text={APP_DOMAIN} : {APP_TYPE} : Ошибка при создании резервной копии: {e}&disable_notification=true"
    print(requests.get(url).json())

except Exception as e:
    print(f"Произошла ошибка: {e}")

    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage?chat_id={TG_CHAT_ID}&text={APP_DOMAIN} : {APP_TYPE} : Произошла ошибка при создании резервной копии: {e}&disable_notification=true"
    print(requests.get(url).json())

finally:
    if "conn" in locals():
        conn.close()
