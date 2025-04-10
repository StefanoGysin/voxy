from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel # Manter import do SQLModel

from ..core.config import settings
from fastapi import HTTPException

# URL de conexão do .env
connection_string = settings.SUPABASE_CONNECTION_STRING
async_engine = None
AsyncSessionFactory = None

if not connection_string:
    print("ALERTA: SUPABASE_CONNECTION_STRING não está definida no .env!")
else:
    # Garantir que a string de conexão use o driver asyncpg
    if connection_string.startswith("postgresql://"):
        async_connection_string = connection_string.replace(
            "postgresql://", "postgresql+asyncpg://", 1
        )
        print(f"Usando driver asyncpg. Nova string: {async_connection_string}")
    elif not connection_string.startswith("postgresql+asyncpg://"):
        # Levantar erro se for outro tipo de DB não esperado ou formato incorreto
        raise ValueError(
            "SUPABASE_CONNECTION_STRING deve começar com 'postgresql://' ou 'postgresql+asyncpg://'"
        )
    else:
        async_connection_string = connection_string # Já está correto

    # Usar create_async_engine com a string corrigida e NullPool
    async_engine = create_async_engine(
        async_connection_string, 
        echo=settings.DEBUG, 
        poolclass=NullPool # Desabilitar pool interno do SQLAlchemy
    )

    # Criar uma fábrica de sessões assíncronas
    # expire_on_commit=False é geralmente recomendado para FastAPI
    AsyncSessionFactory = sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )

async def get_db() -> AsyncSession:
    """
    Dependência FastAPI para obter uma AsyncSession do banco de dados.
    Garante commit/rollback e fechamento da sessão após a requisição.
    """
    if AsyncSessionFactory is None:
        raise HTTPException(
            status_code=503, # Service Unavailable
            detail="Database connection is not configured."
        )

    async with AsyncSessionFactory() as session:
        try:
            yield session
            print("Request successful, attempting commit.") # Log de commit
            await session.commit()
        except Exception as e:
            print(f"Exception during request, rolling back session: {e}")
            await session.rollback()
            raise
        finally:
            # O bloco async with já garante o fechamento da sessão
            print("Closing session via async with context manager")

async def create_db_and_tables():
    """ Cria as tabelas no banco de dados de forma assíncrona. """
    if async_engine:
        print("Tentando criar tabelas do banco de dados (async)...")
        try:
            async with async_engine.begin() as conn:
                # Usar conn.run_sync para operações de metadados que podem não ser async
                await conn.run_sync(SQLModel.metadata.create_all)
            print("Tabelas criadas com sucesso (async) (ou já existiam).")
        except Exception as e:
            print(f"Erro ao criar tabelas (async): {e}")
    else:
        print("Skipping table creation because async database engine is not configured.")

# Nota: A função create_db_and_tables agora é assíncrona e usa conn.run_sync
# para compatibilidade com a criação de metadados.

# Nota: A importação de SQLModel dentro da função é uma forma de evitar 
# problemas de importação circular se os modelos dependerem da engine/session.
# Se não houver dependência circular, pode importar no topo do arquivo. 