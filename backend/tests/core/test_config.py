# backend/tests/core/test_config.py

import os
import pytest
from unittest.mock import patch
from pydantic import ValidationError

# Importar a classe Settings e a instância settings
# Precisamos importar de uma maneira que permita recarregar as configurações
# durante os testes

@pytest.fixture(autouse=True)
def clear_env_vars(monkeypatch):
    """Limpa variáveis de ambiente relevantes antes de cada teste."""
    vars_to_clear = [
        "APP_NAME", "API_PREFIX", "DEBUG", "SECRET_KEY",
        "ALGORITHM", "ACCESS_TOKEN_EXPIRE_MINUTES", "OPENAI_API_KEY",
        "OPENWEATHERMAP_API_KEY", "SUPABASE_URL", "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_CONNECTION_STRING",
        "TEST_DATABASE_URL", "CORS_ORIGINS"
    ]
    for var in vars_to_clear:
        monkeypatch.delenv(var, raising=False)
    # Importante: Precisamos forçar o pydantic-settings a recarregar
    # a configuração após modificar o ambiente. A forma mais simples
    # é reimportar o módulo config ou re-instanciar Settings.
    # Usaremos re-instanciação.


def reload_settings():
    """Recarrega as configurações instanciando Settings novamente."""
    # Isso é crucial porque pydantic-settings pode cachear a leitura do .env
    # e das variáveis de ambiente na primeira importação.
    from app.core.config import Settings
    # Passar _env_file=None para evitar que leia o .env real nos testes,
    # focando apenas nas variáveis de ambiente que definimos com monkeypatch.
    # O _case_sensitive e _extra podem ser mantidos como no original.
    return Settings(_env_file=None, _case_sensitive=True, _extra='ignore') 

def test_default_settings(clear_env_vars): # Usa o fixture para limpar env
    """Testa se os valores padrão são carregados corretamente."""
    settings = reload_settings()
    assert settings.APP_NAME == "Voxy"
    assert settings.API_PREFIX == "/api"
    assert settings.DEBUG is False
    assert settings.SECRET_KEY == "desenvolvimento_inseguro_chave" # Padrão do os.getenv
    assert settings.ALGORITHM == "HS256"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
    assert settings.CORS_ORIGINS == ["*"]
    assert settings.OPENAI_API_KEY is None
    assert settings.OPENWEATHERMAP_API_KEY is None
    assert settings.SUPABASE_URL is None
    assert settings.SUPABASE_ANON_KEY is None
    assert settings.SUPABASE_SERVICE_ROLE_KEY is None
    assert settings.SUPABASE_CONNECTION_STRING is None
    assert settings.TEST_DATABASE_URL is None

def test_environment_variable_override(monkeypatch, clear_env_vars):
    """Testa se as variáveis de ambiente sobrescrevem os padrões."""
    monkeypatch.setenv("APP_NAME", "VoxyTest")
    monkeypatch.setenv("DEBUG", "true") # Testar string booleana
    monkeypatch.setenv("SECRET_KEY", "teste_chave_segura")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60") # Testar string int
    monkeypatch.setenv("OPENAI_API_KEY", "sk-12345")
    monkeypatch.setenv("SUPABASE_URL", "http://localhost:54321")
    monkeypatch.setenv("CORS_ORIGINS", '["http://localhost:3000", "http://test.com"]') # Testar lista string

    settings = reload_settings()
    assert settings.APP_NAME == "VoxyTest"
    assert settings.DEBUG is True
    assert settings.SECRET_KEY == "teste_chave_segura"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60
    assert settings.OPENAI_API_KEY == "sk-12345"
    assert settings.SUPABASE_URL == "http://localhost:54321"
    # Pydantic < v2 tratava JSON strings automaticamente, v2 pode precisar de ajuda
    # Vamos verificar o tipo e o valor
    assert isinstance(settings.CORS_ORIGINS, list)
    assert settings.CORS_ORIGINS == ["http://localhost:3000", "http://test.com"] 

def test_validation_error(monkeypatch, clear_env_vars):
    """Testa se um tipo inválido para um campo causa ValidationError."""
    # ACCESS_TOKEN_EXPIRE_MINUTES espera um int
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "nao-e-numero")
    
    with pytest.raises(ValidationError):
        reload_settings()

def test_extra_variables_ignored(monkeypatch, clear_env_vars):
    """Testa se variáveis de ambiente extras são ignoradas (extra='ignore')."""
    monkeypatch.setenv("VARIAVEL_EXTRA_NAO_DEFINIDA", "valor_extra")
    # Tenta carregar as configurações. Não deve levantar erro.
    try:
        settings = reload_settings()
    except Exception as e:
        pytest.fail(f"Carregar configurações com variável extra levantou erro: {e}")
    
    # Verifica se o atributo extra não foi adicionado ao objeto settings
    assert not hasattr(settings, "VARIAVEL_EXTRA_NAO_DEFINIDA")

# Teste para verificar se SECRET_KEY padrão é usado se a variável não existe
def test_secret_key_default_fallback(clear_env_vars):
    """Testa se o fallback default do os.getenv para SECRET_KEY funciona."""
    # Garantir que a variável NÃO está definida (clear_env_vars faz isso)
    settings = reload_settings()
    assert settings.SECRET_KEY == "desenvolvimento_inseguro_chave"

# Teste para verificar se SECRET_KEY do ambiente é usada quando existe
def test_secret_key_env_override(monkeypatch, clear_env_vars):
    """Testa se a variável de ambiente SECRET_KEY sobrescreve o fallback."""
    monkeypatch.setenv("SECRET_KEY", "chave_do_ambiente_teste")
    settings = reload_settings()
    assert settings.SECRET_KEY == "chave_do_ambiente_teste" 