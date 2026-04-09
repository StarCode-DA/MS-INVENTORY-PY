"""
Configuración del microservicio inventario - Eclipse Bar
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    
    # APP
    APP_NAME: str = "EclipseBar Inventory Service"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1/inventarios"
    DEBUG: bool = True

    # DATABASE
    DATABASE_URL: str = "postgresql://admin:admin@postgres:5432/eclipsebar_db"

    # JWT
    SECRET_KEY: str = "super-secret-key-change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # SERVER
    SERVICE_HOST: str = "0.0.0.0"
    SERVICE_PORT: int = 8004

    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


# instancia global
settings = Settings()