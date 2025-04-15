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
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # Configurações de segurança
    SECRET_KEY: str = os.getenv("SECRET_KEY", "desenvolvimento_inseguro_chave")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Configurações OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # Configurações OpenWeatherMap (Nova)
    OPENWEATHERMAP_API_KEY: Optional[str] = None
    
    # Configurações Supabase (para Mem0 e Client)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None # Chave anônima pública
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_CONNECTION_STRING: Optional[str] = None
    
    # Configurações Banco de Dados (para SQLAlchemy/SQLModel)
    # DATABASE_URL: str # Adicionar se usar DB principal além de Supabase para tabelas custom
    TEST_DATABASE_URL: Optional[str] = None # Para o banco de dados de teste
    
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