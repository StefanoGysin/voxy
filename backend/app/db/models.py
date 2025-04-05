from typing import Optional
from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    """ Modelo base com campos comuns, sem ID e sem segredos. """
    username: str = Field(index=True, unique=True)
    # Adicionar outros campos públicos se necessário (ex: email, full_name)


class User(UserBase, table=True):
    """ Modelo de tabela do banco de dados, inclui ID e campos secretos. """
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    # Definir nome da tabela explicitamente (opcional, mas bom)
    # __tablename__ = "users" 


class UserCreate(UserBase):
    """ Modelo Pydantic para criar um novo usuário (recebe senha). """
    password: str


class UserRead(UserBase):
    """ Modelo Pydantic para ler/retornar dados de usuário (sem senha). """
    id: int

# Adicionar outros modelos conforme necessário (ex: Token, Message, etc.) 