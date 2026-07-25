"""FastAPI entrypoint: wires routers, seeds data, and serves the built SPA."""
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from .core import config
from .core.database import Base, SessionLocal, engine
from .routers import auth, documents, folders, notifications, shares, uploads, ws
from .seed import seed

# Fail fast: never run a production (HTTPS) deploy with the default JWT secret,
# which would let anyone forge tokens.
if config.COOKIE_SECURE and config.SESSION_SECRET == "dev-secret-change-me":
    raise RuntimeError(
        "SESSION_SECRET must be set to a strong value in production "
        "(COOKIE_SECURE=1)."
    )

app = FastAPI(title="Ajaia Docs API")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Add conservative security headers to every response."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "img-src 'self' data:; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; "
        # Fonts are served from same-origin /assets, but the Vite build inlines
        # small subsets as data: URIs — allow both. (Fonts can't execute code.)
        "font-src 'self' data:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    return response

# In local dev the Vite server (5173) calls the API (8000) cross-origin.
# In production everything is same-origin, so this is dev-only convenience.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(shares.router)
app.include_router(uploads.router)
app.include_router(notifications.router)
app.include_router(folders.router)
app.include_router(ws.router)


def ensure_schema():
    """Create new tables and add columns added since an existing DB was created.

    A lightweight stand-in for full migrations (e.g. Alembic): create_all() makes
    new tables, and we additively backfill known new columns on existing tables so
    a persistent Postgres from an earlier release keeps working after a deploy.
    """
    Base.metadata.create_all(bind=engine)
    insp = inspect(engine)
    if insp.has_table("documents"):
        cols = {c["name"] for c in insp.get_columns("documents")}
        if "folder_id" not in cols:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE documents ADD COLUMN folder_id INTEGER"))


@app.on_event("startup")
def on_startup():
    ensure_schema()
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


@app.get("/api/health")
def health():
    # Report the DB backend + whether LLM chat is configured (both non-sensitive).
    return {"status": "ok", "db": engine.dialect.name, "llm": config.LLM_ENABLED}


# --- Serve the built frontend (production single-service deploy) -------------
_dist = os.path.abspath(config.FRONTEND_DIST)
if os.path.isdir(_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        """Serve static files when present, else fall back to index.html (SPA routes)."""
        candidate = os.path.join(_dist, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(_dist, "index.html"))
