"""Web entrypoint for CSCN_portal.

Bootstraps logging + database + seeding (reusing main.py's helpers), then serves
the FastAPI app (JSON API + React SPA) via uvicorn. Replaces the Qt entrypoint
(main.py) for the web build.
"""
import os
import sys

# In a --windowed (no-console) PyInstaller build, sys.stdout/sys.stderr are None.
# Several libraries (uvicorn's log formatter, loguru's console sink) call
# .isatty()/.write() on them and crash. Give them a real sink before anything
# else imports/configures logging.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

from loguru import logger

from config.logging_config import setup_logging


def _install_excepthook():
    def _hook(exc_type, exc, tb):
        logger.opt(exception=(exc_type, exc, tb)).error("Uncaught exception")
        sys.__excepthook__(exc_type, exc, tb)
    sys.excepthook = _hook


def bootstrap():
    """Create the schema, seed initial data, and enforce permissions. Returns the
    FastAPI app instance."""
    from database.base import Base
    from database.engine import engine
    import domain.entities  # noqa: F401  -- registers all models on Base.metadata
    from database.session import db_session as scoped_db_session
    from main import seed_initial_data, reconcile_permissions, ensure_default_accounts
    from api.config_api import get_session_secret

    Base.metadata.create_all(engine)
    db = scoped_db_session()
    try:
        seed_initial_data(db)
        ensure_default_accounts(db)   # self-heal: never end up with zero accounts
        reconcile_permissions(db)
        # Flush the WAL into the main .db so seeded data survives a hard kill.
        try:
            with engine.connect() as conn:
                conn.exec_driver_sql("PRAGMA wal_checkpoint(TRUNCATE)")
        except Exception:
            pass
    finally:
        scoped_db_session.remove()

    get_session_secret()  # ensure a stable session secret exists/persisted

    # Start the LAN peer server so other portals can pull data/logs from this
    # one (used by the "remote portals" screen). Daemon thread; never fatal.
    try:
        from application.services.peer_server import PeerServer
        PeerServer().start()
    except Exception:
        logger.warning("Peer server could not be started; remote pull disabled.")

    from api.app import create_app
    return create_app()


def main():
    setup_logging()
    _install_excepthook()
    try:
        app = bootstrap()
        import launcher
        launcher.run(app)
    except SystemExit:
        raise
    except Exception:
        logger.exception("Fatal error during web application startup")
        raise


if __name__ == "__main__":
    main()
