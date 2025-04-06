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

def decode_access_token(token: str) -> TokenData | None:
    """
    Decodifica um token JWT e retorna os dados do payload se válido.

    Args:
        token (str): O token JWT a ser decodificado.

    Returns:
        TokenData | None: Um objeto TokenData com o username (sub) se o token
                          for válido e não expirado, None caso contrário.
    """
    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM]
        )
        username: str | None = payload.get("sub")
        if username is None:
            # Token válido, mas sem 'sub' não é esperado
            return None 
        # TODO: Adicionar validação de expiração se 'decode' não fizer por padrão
        # com as opções corretas, mas geralmente faz.
        token_data = TokenData(username=username)
        return token_data
    except JWTError: 
        # Token inválido (formato, assinatura, expiração, etc.)
        return None

async def get_current_user(
    session: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependência FastAPI para obter o usuário atual a partir do token JWT.

    Decodifica o token usando decode_access_token, valida o username (sub)
    e busca o usuário no DB.

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
    
    token_data = decode_access_token(token)
    if token_data is None or token_data.username is None:
        raise credentials_exception
    
    # Buscar usuário no banco de dados
    # ATENÇÃO: O modelo User usa 'email' como identificador único, não 'username'.
    # O token 'sub' deve conter o email.
    user = session.exec(
        select(User).where(User.email == token_data.username)
    ).first()
    
    if user is None:
        raise credentials_exception
    return user

# Poderíamos adicionar get_current_active_user se tivéssemos um campo 'is_active' no modelo User 