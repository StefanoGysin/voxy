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
# Importar cliente Supabase e dependência
from supabase import Client
from app.db.supabase_client import get_supabase_client

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

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Cria um novo token de acesso JWT.

    Args:
        data (dict): Dados a serem incluídos no payload (geralmente {"sub": username}).
        expires_delta (timedelta | None): Duração opcional da validade do token.
                                           Se None, usa o padrão das configurações.

    Returns:
        str: O token JWT codificado.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Remover decode_access_token, pois a validação será feita pelo Supabase
# def decode_access_token(token: str) -> TokenData | None:
#    ...

# Modificar get_current_user para usar Supabase Auth
async def get_current_user(
    # Remover dependência do DB local (session)
    # session: AsyncSession = Depends(get_db),
    supabase: Client = Depends(get_supabase_client), # Adicionar cliente Supabase
    token: str = Depends(oauth2_scheme)
#) -> Tuple[User, str]: # Modificar tipo de retorno
) -> Any: # Retorna o objeto User do Supabase (ou Any para simplificar)
    """
    Dependência FastAPI para obter o usuário atual validando o token JWT
    com o Supabase Auth.

    Args:
        supabase (Client): Cliente Supabase injetado.
        token (str): Token JWT obtido do cabeçalho Authorization Bearer.

    Raises:
        HTTPException (401): Se o token for inválido ou expirado.

    Returns:
        Any: O objeto User retornado por supabase.auth.get_user(), que contém
             informações do usuário autenticado (incluindo id/UUID).
             Retornando Any por simplicidade, pode ser tipado melhor se necessário.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        print("Attempting to get user from Supabase Auth with token...")
        # Validar o token e obter o usuário diretamente do Supabase Auth
        response = supabase.auth.get_user(token)
        print("Supabase Auth get_user response received.")
        
        # Verificar se o usuário foi retornado com sucesso
        if response.user is None:
            print(f"Supabase Auth get_user failed. Response: {response}")
            raise credentials_exception
        
        print(f"Supabase Auth get_user successful. User ID: {response.user.id}")
        # Retorna o objeto User do Supabase
        # Este objeto contém o 'id' (UUID), 'email', 'aud', 'role', etc.
        return response.user 

    except Exception as e:
        # Captura erros gerais (ex: token mal formatado, erro de rede, etc.)
        print(f"Exception during Supabase get_user: {e}")
        raise credentials_exception

# A função antiga que buscava no DB local é removida ou comentada.
# async def get_current_user_local_db(...)

# Poderíamos adicionar get_current_active_user se tivéssemos um campo 'is_active' no modelo User 