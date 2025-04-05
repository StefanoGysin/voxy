from sqlmodel import create_engine, Session
from ..core.config import settings
from fastapi import HTTPException

# URL de conexão do .env
connection_string = settings.SUPABASE_CONNECTION_STRING

if not connection_string:
    # Log ou raise error se a string de conexão não estiver definida
    # Por enquanto, vamos permitir que continue, mas a criação da engine falhará
    print("ALERTA: SUPABASE_CONNECTION_STRING não está definida no .env!")
    # Você pode querer levantar um erro aqui em produção:
    # raise ValueError("SUPABASE_CONNECTION_STRING must be set in environment variables")
    # Usar um DB em memória como fallback para desenvolvimento local sem Supabase?
    # connection_string = "sqlite:///./local_dev.db"
    # engine = create_engine(connection_string, echo=True, connect_args={"check_same_thread": False})
    engine = None # Define engine como None se não houver connection string
else:
    # connect_args só é necessário para SQLite
    # echo=True loga as queries SQL - útil para debug, remover em produção
    engine = create_engine(connection_string, echo=settings.DEBUG)


def get_db():
    """ 
    Dependência FastAPI para obter uma sessão do banco de dados.
    Garante commit/rollback e fechamento da sessão após a requisição.
    """
    if engine is None:
        raise HTTPException(
            status_code=503, # Service Unavailable
            detail="Database connection is not configured."
        )
        
    session = Session(engine)
    try:
        yield session
        # Se a rota executou sem exceção, faz commit aqui.
        print("Request successful, attempting commit.") # Log de commit
        session.commit()
    except Exception as e:
        print(f"Exception during request, rolling back session: {e}")
        session.rollback()
        raise
    finally:
        print("Closing session in finally block")
        session.close()

def create_db_and_tables():
    """ Cria as tabelas no banco de dados se elas não existirem. """
    if engine:
        print("Tentando criar tabelas do banco de dados...")
        try:
            # Importa os metadados DEPOIS da engine ser criada
            # e apenas se a engine foi criada com sucesso.
            from .models import SQLModel # Garante que importa o SQLModel correto
            SQLModel.metadata.create_all(engine)
            print("Tabelas criadas com sucesso (ou já existiam).")
        except Exception as e:
            print(f"Erro ao criar tabelas: {e}")
            # Considerar logar o erro completo aqui
    else:
        print("Skipping table creation because database engine is not configured.")

# Nota: A importação de SQLModel dentro da função é uma forma de evitar 
# problemas de importação circular se os modelos dependerem da engine/session.
# Se não houver dependência circular, pode importar no topo do arquivo. 