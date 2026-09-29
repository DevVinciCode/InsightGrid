"""
Central configuration. Everything environment-dependent lives here so the
rest of the app never hard-codes a provider, database, or path.

To point at a new database or LLM provider, change .env — not code.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Database ---
    DB_TYPE: str = "sqlite"                     # sqlite | postgresql
    DB_PATH: str = "../data/demo_database/demo.db"   # used for sqlite
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "datatalk"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""

    # --- LLM provider ---
    LLM_PROVIDER: str = "rulebased"             # rulebased | openai | groq | gemini
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_BASE_URL: str = ""                      # override for OpenAI-compatible endpoints

    # --- RAG / vector store ---
    VECTOR_STORE: str = "tfidf"                 # tfidf | faiss
    RAG_TOP_K: int = 5

    # --- Safety / execution ---
    SQL_ROW_LIMIT: int = 500
    SQL_TIMEOUT_SECONDS: int = 10
    MAX_SQL_RETRIES: int = 2
    PROBE_ROW_LIMIT: int = 20

    # --- Feature flags (Stage 3+ research modules) ---
    ENABLE_INTENT_ANALYSIS: bool = True
    ENABLE_UNCERTAINTY: bool = True
    ENABLE_DB_PROBING: bool = False        # Stage 3 — scaffolded, not wired in yet
    ENABLE_CLARIFICATION: bool = False     # Stage 3 — scaffolded, not wired in yet
    ENABLE_RESULT_VERIFICATION: bool = True
    ENABLE_POWERBI: bool = False           # Stage 5 — requires a real Azure AD app registration

    # --- Power BI (Stage 5, optional) ---
    POWERBI_TENANT_ID: str = ""
    POWERBI_CLIENT_ID: str = ""
    POWERBI_CLIENT_SECRET: str = ""
    POWERBI_WORKSPACE_ID: str = ""
    POWERBI_DATASET_ID: str = ""
    POWERBI_REPORT_ID: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
