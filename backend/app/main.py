"""
Ponto de entrada principal da aplicação Voxy.

Este módulo configura o aplicativo FastAPI e registra as rotas.
"""

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.chat import router as chat_router

# Carrega variáveis de ambiente do arquivo .env
# Deve ser chamado antes de qualquer código que dependa dessas variáveis
load_dotenv()

app = FastAPI(
    title="Voxy API",
    description="API para interação com o agente Voxy",
    version="0.1.0"
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