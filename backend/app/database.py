import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Expect timescaledb URL to be provided, default to localhost for local runner
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/boxbox")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
