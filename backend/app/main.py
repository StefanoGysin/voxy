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
# Importar o novo router de uploads (NOVO)
from .api.v1.endpoints.uploads import router as uploads_router_v1
# Importar função para inicializar cliente Supabase
from .db.supabase_client import initialize_supabase_client, get_supabase_client
# Importar o novo AuthMiddleware
from .middleware import AuthMiddleware

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
    await initialize_supabase_client() # Usa await para inicializar Supabase
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
# Lista explícita de origens permitidas (incluindo o frontend dev)
allowed_origins = [
    "http://localhost:5173", # Frontend Vite dev
    "http://127.0.0.1:5173", # Outra forma de localhost
    # Adicione outras origens se necessário (ex: produção)
]

app.add_middleware(
    CORSMiddleware,
    # allow_origins=["*"], # Substituído por lista explícita
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"], # Métodos explícitos
    # allow_headers=["*"], # Substituído por lista explícita
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization", # Essencial para autenticação
        "X-Requested-With",
        # Adicione outros cabeçalhos customizados se usar
    ],
)

# Adicionar AuthMiddleware (sem passar o cliente Supabase)
app.add_middleware(AuthMiddleware)
print("AuthMiddleware adicionado com sucesso.")

# Registrar rotas
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
# Registrar as novas rotas do agente v1
app.include_router(agent_router_v1, prefix="/api/v1/agent", tags=["agent_v1"])
# Registrar as novas rotas de uploads v1 (NOVO)
app.include_router(uploads_router_v1, prefix="/api/v1/uploads", tags=["uploads_v1"])


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