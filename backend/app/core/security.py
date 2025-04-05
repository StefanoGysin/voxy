from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Any, Union

from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

# Importar configurações
from .config import settings
from .models import TokenData
from ..db.models import User
from ..db.session import get_db

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
SECRET_KEY = settings.SECRET_KEY # Chave secreta do .env
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# Define o esquema de segurança OAuth2 apontando para a rota de login
# IMPORTANTE: A URL deve corresponder EXATAMENTE à rota do seu endpoint de login
# Se o router de auth for incluído com prefixo, ajuste aqui (ex: "/auth/login")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login") 

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
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Função para decodificar/validar token será adicionada depois (para get_current_user)

async def get_current_user(
    session: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependência FastAPI para obter o usuário atual a partir do token JWT.

    Decodifica o token, valida o username (sub) e busca o usuário no DB.

    Args:
        session (Session): Sessão do banco de dados injetada.
        token (str): Token JWT obtido do cabeçalho Authorization Bearer.

    Raises:
        HTTPException (401): Se o token for inválido, expirado, ou o usuário não existir.

    Returns:
        User: O objeto User correspondente ao token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM]
        )
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    # Buscar usuário no banco de dados
    # TODO: Idealmente usar uma função crud (ex: crud.user.get_user_by_username)
    user = session.exec(
        select(User).where(User.username == token_data.username)
    ).first()
    
    if user is None:
        raise credentials_exception
    return user

# Poderíamos adicionar get_current_active_user se tivéssemos um campo 'is_active' no modelo User 