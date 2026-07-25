"""Central runtime configuration, read once from the environment."""
import os

# SQLite locally by default; set DATABASE_URL to a Postgres URL in production.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./docs.db")

# Render/Heroku hand out "postgres://" URLs; SQLAlchemy wants "postgresql://".
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Secret used to sign JWTs / the session cookie. Override in production.
SESSION_SECRET = os.environ.get("SESSION_SECRET", "dev-secret-change-me")

# Token / cookie lifetime in seconds (7 days).
SESSION_MAX_AGE = 60 * 60 * 24 * 7
COOKIE_NAME = "session"

# Set to "1" in production (HTTPS) so the cookie is only sent over TLS.
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "0") == "1"

# Upload limits for the file-import feature.
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB (.docx files are heavier than text)
ALLOWED_UPLOAD_EXTS = {".txt", ".md", ".docx"}

# LLM (folder RAG chat) via OpenRouter — OpenAI-compatible API. Optional:
# when no key is set, the chat feature is cleanly disabled.
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o")
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
LLM_ENABLED = bool(OPENROUTER_API_KEY)

# Absolute path to the built frontend. This file lives at app/core/config.py, so
# three levels up is the backend dir; the SPA build sits at repo/frontend/dist.
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIST = os.environ.get(
    "FRONTEND_DIST", os.path.join(_BACKEND_DIR, "..", "frontend", "dist")
)
