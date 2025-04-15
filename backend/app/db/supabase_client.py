"""
Gerencia a inicialização e o acesso ao cliente Supabase.
"""

import os
# Importa AsyncClient e acreate_client para uso assíncrono
from supabase import AsyncClient, acreate_client
from app.core.config import settings

# Ajusta a anotação de tipo para AsyncClient
supabase_client: AsyncClient | None = None


async def initialize_supabase_client():
    """
    Inicializa o cliente Supabase assíncrono global usando as configurações.
    
    Raises:
        ValueError: Se as variáveis de ambiente SUPABASE_URL ou 
                    SUPABASE_SERVICE_ROLE_KEY não estiverem definidas.
    """
    global supabase_client
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY devem ser definidos "
            "nas variáveis de ambiente ou no arquivo .env"
        )
    
    # Usa acreate_client para criar cliente assíncrono
    supabase_client = await acreate_client(
        settings.SUPABASE_URL, 
        settings.SUPABASE_SERVICE_ROLE_KEY
    )
    print("Cliente Supabase Assíncrono inicializado.") # Log para confirmação


def get_supabase_client() -> AsyncClient:
    """
    Retorna a instância inicializada do cliente Supabase assíncrono.
    
    Útil como dependência FastAPI.
    
    Returns:
        AsyncClient: A instância do cliente Supabase assíncrono.
        
    Raises:
        RuntimeError: Se o cliente não foi inicializado.
    """
    if supabase_client is None:
        # A inicialização deve ocorrer no lifespan do FastAPI.
        # Levantar um erro aqui é mais seguro do que inicializar sob demanda.
        raise RuntimeError("Cliente Supabase Assíncrono não inicializado. Verifique o lifespan da aplicação.")
         
    return supabase_client

# A inicialização deve ocorrer no lifespan de main.py 