import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base

# Para las pruebas usamos una BBDD SQLite local en la ruta del proyecto
DATABASE_URL = "sqlite:///aem_ledger.db"

# connect_args={"check_same_thread": False} se requiere para SQLite en aplicaciones multihilo (como LangGraph)
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Crea todas las tablas si no existen en la base de datos local."""
    Base.metadata.create_all(bind=engine)
