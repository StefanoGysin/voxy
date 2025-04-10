"""
Gerencia a inicialização e o acesso ao cliente Supabase.
"""

import os
from supabase import create_client, Client
from app.core.config import settings

supabase_client: Client | None = None


def initialize_supabase_client():
    """
    Inicializa o cliente Supabase global usando as configurações.
    
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
    
    supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    print("Cliente Supabase inicializado.") # Log para confirmação


def get_supabase_client() -> Client:
    """
    Retorna a instância inicializada do cliente Supabase.
    
    Útil como dependência FastAPI.
    
    Returns:
        Client: A instância do cliente Supabase.
        
    Raises:
        RuntimeError: Se o cliente não foi inicializado.
    """
    if supabase_client is None:
        # Em um cenário de produção, a inicialização deve ocorrer no startup do FastAPI.
        # Para simplificar agora, podemos tentar inicializar aqui, mas idealmente
        # a inicialização deve ser garantida antes de qualquer requisição.
        # raise RuntimeError("Cliente Supabase não inicializado. Chame initialize_supabase_client() no startup.")
        # Por enquanto, vamos tentar inicializar se for None
        print("Aviso: Cliente Supabase sendo inicializado sob demanda. Considere inicializar no startup.")
        initialize_supabase_client()

    # Verifica novamente após a tentativa de inicialização
    if supabase_client is None:
         raise RuntimeError("Falha ao inicializar o cliente Supabase.")
         
    return supabase_client

# Opcional: Chamar initialize_supabase_client() aqui se não for feito no startup do FastAPI
# No entanto, é melhor prática registrar eventos de startup/shutdown no FastAPI
# initialize_supabase_client() 