"""API routers. ``all_routers`` is the ordered list mounted by create_app()."""
from api.routers import (
    auth, dashboard, hr, lookups, standards, records, documents,
    financial, partnerships, training, reports, admin, backup, remote, settings,
)

all_routers = [
    auth.router,
    dashboard.router,
    hr.router,
    lookups.router,
    standards.router,
    records.router,
    documents.router,
    financial.router,
    partnerships.router,
    training.router,
    reports.router,
    admin.router,
    backup.router,
    remote.router,
    settings.router,
]
