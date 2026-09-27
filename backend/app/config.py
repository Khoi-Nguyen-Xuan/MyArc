from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24

    # AI pipeline. Passed to the clients explicitly: pydantic-settings reads .env
    # into this object but doesn't put the values into os.environ.
    openai_api_key: str = ""
    tavily_api_key: str = ""
    llm_model: str = "openai:gpt-5-mini"
    reddit_user_agent: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""

    # ignore unrelated vars in .env (POSTGRES_USER/PASSWORD/DB are only
    # read by docker-compose, not by this app)
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
