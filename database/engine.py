from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from config.settings import DATABASE_URL

# Create the SQLAlchemy engine
# connect_args={"check_same_thread": False} is required for SQLite in multi-threaded environments
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    connect_args={"check_same_thread": False}
)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Enable foreign key constraints and WAL mode for SQLite
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    # Wait up to 5s for a lock instead of failing immediately with
    # "database is locked" — matters once several LAN clients write concurrently.
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()
