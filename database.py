from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy.orm import declarative_base
import os

# Load environment variables from .env file
load_dotenv(dotenv_path=Path(__file__).parent / ".env")
# Construct the database URL
DATABASE_URL = os.getenv("DATABASE_URL")

# Create the database engine
engine = create_engine(DATABASE_URL)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Create a base
Base = declarative_base()

# Example function to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()