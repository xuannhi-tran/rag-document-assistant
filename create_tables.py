from app.database import Base, engine
from app.models import Document, Chunk

Base.metadata.create_all(bind=engine)