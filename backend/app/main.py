"""
Ponto de entrada principal da aplicação Voxy.

Este módulo configura o aplicativo FastAPI e registra as rotas.
"""

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager # Para eventos startup/shutdown
from .api.chat import router as chat_router
# Importar novo router de autenticação
from .api.auth import router as auth_router
# Importar função para criar tabelas
from .db.session import create_db_and_tables 

# Carrega variáveis de ambiente do arquivo .env
# Deve ser chamado antes de qualquer código que dependa dessas variáveis
load_dotenv()

# --- Ciclo de Vida da Aplicação (Startup/Shutdown) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código a ser executado ANTES do startup
    print("Iniciando aplicação Voxy...")
    print("Verificando e criando tabelas do banco de dados...")
    create_db_and_tables() # Chama a função para criar tabelas
    yield
    # Código a ser executado APÓS o shutdown
    print("Encerrando aplicação Voxy...")

app = FastAPI(
    title="Voxy API",
    description="API para interação com o agente Voxy",
    version="0.1.0",
    lifespan=lifespan # Adiciona o gerenciador de ciclo de vida
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique origens permitidas
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rotas
app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])


@app.get("/")
async def root():
    """
    Endpoint raiz que retorna informações básicas da API.
    
    Returns:
        Informações básicas sobre a API.
    """
    return {
        "name": "Voxy API",
        "version": "0.1.0",
        "description": "API para interação com o agente Voxy"
    }


@app.get("/health")
async def health_check():
    """
    Endpoint para verificação de saúde da API.
    
    Returns:
        Status de saúde da API.
    """
    return {"status": "healthy"} 