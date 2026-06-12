# 
# ─────────────────────────────────────────────────────────────────────────────

# ── MySQL ─────────────────────────────────────────────────────────────────────
DB_USER     = "root"           
DB_PASSWORD = "111"   
DB_HOST     = "localhost"
DB_PORT     = 3306
DB_NAME     = "flowtask"

# ── Anthropic ─────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = ""
ANTHROPIC_MODEL   = "claude-sonnet-4-20250514"

# ── Flask ─────────────────────────────────────────────────────────────────────
SECRET_KEY = " "

# ── Auto-built DB URI ─────────────────────────────────────────────────────────
SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False
DB_PASSWORD = "111"
ANTHROPIC_API_KEY = ""  # paste your real key