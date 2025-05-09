from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine

# Define the base for all models
Base = declarative_base()

# Setup DB engine and session
engine = create_engine("sqlite:///manifold.db", echo=False)
SessionLocal = sessionmaker(bind=engine)
