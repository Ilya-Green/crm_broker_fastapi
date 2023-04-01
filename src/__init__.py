from sqlalchemy import create_engine

from .config import DB_URI, DB_FILE

engine = create_engine(DB_URI+DB_FILE, connect_args={"check_same_thread": False}, echo=False)
