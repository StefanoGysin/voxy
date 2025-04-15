from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Any, Union, Tuple

from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
# Remover imports relacionados ao DB local se não forem mais usados para User
# from sqlmodel import Session, select 
# from sqlalchemy.ext.asyncio import AsyncSession

# Importar configurações
from .config import settings
from .models import TokenData
# Importar AsyncClient e Client
from supabase import Client, AsyncClient
from app.db.supabase_client import get_supabase_client
# Importar exceções customizadas
from .exceptions import DatabaseError

# Configura o contexto do passlib
# Usaremos bcrypt como o esquema de hashing principal
# 'deprecated="auto"' fará com que esquemas mais antigos sejam atualizados automaticamente
# no futuro, se necessário.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se uma senha em texto plano corresponde a um hash.

    Args:
        plain_password (str): A senha em texto plano.
        hashed_password (str): O hash da senha armazenado.

    Returns:
        bool: True se a senha corresponder, False caso contrário.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Gera o hash de uma senha em texto plano.

    Args:
        password (str): A senha em texto plano a ser hasheada.

    Returns:
        str: O hash da senha gerado.
    """
    return pwd_context.hash(password)

# Funções para JWT serão adicionadas aqui posteriormente 

# --- Funções JWT --- 

ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Modificar get_current_user para ser async e usar AsyncClient
async def get_current_user(
    # Injetar AsyncClient em vez de Client
    supabase: AsyncClient = Depends(get_supabase_client),
    token: str = Depends(oauth2_scheme)
) -> Any: # Retorna o objeto User do Supabase (ou Any para simplificar)
    """
    Dependência FastAPI para obter o usuário atual validando o token JWT
    com o Supabase Auth de forma assíncrona.

    Args:
        supabase (AsyncClient): Cliente Supabase assíncrono injetado.
        token (str): Token JWT obtido do cabeçalho Authorization Bearer.

    Raises:
        HTTPException (401): Se o token for inválido ou expirado.

    Returns:
        Any: O objeto User retornado por supabase.auth.get_user(), que contém
             informações do usuário autenticado.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        print("Attempting to get user from Supabase Auth with token (async)...")
        # Validar o token e obter o usuário diretamente do Supabase Auth (agora com await)
        response = await supabase.auth.get_user(token)
        print("Supabase Auth get_user response received (async).")

        # Verificar se o usuário foi retornado com sucesso
        if response.user is None:
            print(f"Supabase Auth get_user failed (async). Response: {response}")
            raise credentials_exception

        print(f"Supabase Auth get_user successful (async). User ID: {response.user.id}")
        # Retorna o objeto User do Supabase
        return response.user

    except Exception as e:
        # Captura erros gerais e levanta a exceção de credenciais
        # Idealmente, poderíamos capturar exceções específicas do supabase-py se disponíveis
        print(f"Exception during Supabase get_user (async): {e}")
        # Poderia levantar DatabaseError aqui, mas HTTPException é mais direto para a API
        raise credentials_exception

# A função antiga que buscava no DB local é removida ou comentada.
# async def get_current_user_local_db(...)

# Poderíamos adicionar get_current_active_user se tivéssemos um campo 'is_active' no modelo User 