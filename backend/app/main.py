"""
Ponto de entrada principal da aplicação Voxy.

Este módulo configura o aplicativo FastAPI e registra as rotas.
"""

import logging # Adicionado
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager # Para eventos startup/shutdown
# Importar novo router de autenticação
from .api.auth import router as auth_router
# Importar o novo router do agente
from .api.v1.endpoints.agent import router as agent_router_v1
# Importar função para inicializar cliente Supabase
from .db.supabase_client import initialize_supabase_client

# --- Configuração de Logging --- # Modificado
# Define o nível base como DEBUG para capturar nossos logs customizados
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Reduz a verbosidade de bibliotecas específicas
logging.getLogger("httpcore").setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.INFO)
logging.getLogger("openai").setLevel(logging.WARNING) # OpenAI pode ser bem verboso, WARNING pode ser melhor
logging.getLogger("openai.agents").setLevel(logging.INFO) # Manter INFO para ver chamadas de ferramenta
logging.getLogger("mem0").setLevel(logging.INFO) # Logs da biblioteca mem0
logging.getLogger("mem0ai").setLevel(logging.INFO) # Logs da biblioteca mem0ai (caso o import mude)
logging.getLogger("hpack").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING) # Silencia logs de acesso Uvicorn

# Carrega variáveis de ambiente do arquivo .env
# Deve ser chamado antes de qualquer código que dependa dessas variáveis
load_dotenv()

# --- Ciclo de Vida da Aplicação (Startup/Shutdown) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código a ser executado ANTES do startup
    print("Iniciando aplicação Voxy...")
    print("Inicializando cliente Supabase...")
    initialize_supabase_client() # Chama a função para inicializar Supabase
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
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
# Registrar as novas rotas do agente v1
app.include_router(agent_router_v1, prefix="/api/v1/agent", tags=["agent_v1"])


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