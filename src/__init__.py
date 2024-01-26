from sqlalchemy import create_engine

from .config import DB_URI, DB_FILE

engine = create_engine(DB_URI+DB_FILE, execution_options={"batch_mode": True}, echo=False)
