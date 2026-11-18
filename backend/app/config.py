from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # SQLite works out of the box; set postgresql+psycopg://user:pass@host:5432/fitfinder for Postgres.
    database_url: str = "sqlite:///./fitfinder.db"
    # Optional. When set, natural-language search is parsed by GPT-4o; otherwise the built-in parser runs.
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o"
    openai_timeout_s: float = 8.0
    # Load a catalog on startup when the products table is empty.
    auto_seed: bool = True
    # "real": products and size charts scraped from real Indian stores (data/real_catalog.json).
    # "demo": the original synthetic catalog of 8 fictional brands (data/seed_catalog.json).
    catalog: str = "real"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def sqlalchemy_url(self) -> str:
        url = self.database_url
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://"):]
        return url


settings = Settings()
