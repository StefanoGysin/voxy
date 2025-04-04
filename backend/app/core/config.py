"""
Configurações do aplicativo Voxy.

Este módulo gerencia as configurações do aplicativo, incluindo 
variáveis de ambiente, configurações do modelo, etc.
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    """
    Configurações do aplicativo usando Pydantic para validação.
    
    Isso permite validar as configurações e fornecer valores padrão.
    Carrega automaticamente variáveis de ambiente e de um arquivo .env.
    """
    
    # Configurações gerais
    APP_NAME: str = "Voxy"
    API_PREFIX: str = "/api"
    DEBUG: bool = False
    
    # Configurações de segurança
    SECRET_KEY: str = os.getenv("SECRET_KEY", "desenvolvimento_inseguro_chave")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Configurações OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # Configurações OpenWeatherMap (Nova)
    OPENWEATHERMAP_API_KEY: Optional[str] = None
    
    # Configurações CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # Nova forma de configurar o Pydantic Settings (substitui a classe Config)
    model_config = SettingsConfigDict(
        env_file=".env", 
        case_sensitive=True, 
        extra="ignore" # Ignora variáveis de ambiente extras não definidas no modelo
    )


# Instância de configurações para fácil importação
settings = Settings()


def get_settings() -> Settings:
    """
    Retorna a instância global das configurações.
    
    Útil para injeção de dependência no FastAPI.
    
    Returns:
        Settings: A instância global das configurações.
    """
    return settings 