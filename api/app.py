"""FastAPI application factory.

Serves the JSON REST API under /api/* and the built React SPA for every other
path (client-side routing). Auth is a signed session cookie (same origin as the
SPA, so no CORS/JWT needed).
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from api.config_api import get_session_secret, SESSION_MAX_AGE, REMEMBER_MAX_AGE, FRONTEND_DIST
from api.middleware import CurrentUserMiddleware
from api.routers import all_routers


def create_app() -> FastAPI:
    app = FastAPI(title="CSCN_portal", docs_url="/api/docs", openapi_url="/api/openapi.json")

    # Order matters: add the current-user middleware FIRST so SessionMiddleware
    # (added second => outermost) runs before it and populates request.session.
    app.add_middleware(CurrentUserMiddleware)
    app.add_middleware(
        SessionMiddleware,
        secret_key=get_session_secret(),
        session_cookie="cscn_session",
        max_age=REMEMBER_MAX_AGE,   # ceiling; short sessions are enforced server-side if needed
        same_site="lax",
        https_only=False,
    )

    for router in all_routers:
        app.include_router(router)

    @app.get("/api/healthz")
    def healthz():
        return {"status": "ok"}

    # ----------------------------------------------------------- SPA serving
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    index_file = FRONTEND_DIST / "index.html"

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        # /api/* is handled by routers above; anything else returns the SPA shell
        # so the React router can take over.
        if full_path.startswith("api/"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        # Serve a real static file if it exists (favicon, fonts, etc.)
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(str(candidate))
        if index_file.exists():
            return FileResponse(str(index_file))
        return HTMLResponse(
            "<h1>CSCN_portal</h1><p>الواجهة لم تُبنَ بعد. شغّل: "
            "<code>npm --prefix frontend run build</code></p>",
            status_code=200,
        )

    return app
