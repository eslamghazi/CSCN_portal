from sqlalchemy.orm import sessionmaker, scoped_session
from database.engine import engine

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Scoped session for thread safety
db_session = scoped_session(SessionLocal)

def get_db():
    """
    Dependency generator that provides a database session.
    """
    db = db_session()
    try:
        yield db
    finally:
        db.close()
