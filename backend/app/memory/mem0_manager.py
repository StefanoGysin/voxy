import asyncio
import logging
import functools
import contextvars
from typing import List, Dict, Any, Optional

# Define o logger ANTES de tentar usá-lo no bloco de importação
logger = logging.getLogger(__name__)

# Importar Memory (síncrona)
try:
    # Tenta importar de mem0 primeiro, pois é o namespace mais provável agora
    from mem0 import Memory
except ImportError:
    try:
        # Fallback para mem0ai se o primeiro falhar
        from mem0ai import Memory 
        logger.warning("Importado 'Memory' de 'mem0ai'. Verifique se 'mem0' deveria ser o namespace.")
    except ImportError:
        logger.error("Falha ao importar 'Memory' de 'mem0' ou 'mem0ai'. Verifique a instalação.")
        class Memory: # Placeholder
            def __init__(self, *args, **kwargs): raise ImportError("Memory não pôde ser importado.")
            @classmethod
            def from_config(cls, *args, **kwargs): raise ImportError("Memory não pôde ser importado.")

# Remover import desnecessário
# try:
#     from mem0 import AsyncMemoryClient
# except ImportError:
#     logger.error("Falha ao importar AsyncMemoryClient de 'mem0'...")
#     class AsyncMemoryClient: ...

from ..core.config import settings

# Definir o ContextVar para o user_id atual
# Usar Union[str, int] se o ID puder ser int
current_user_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "current_user_id", default=None
)

class Mem0Manager:
    """
    Gerencia a interação com a biblioteca mem0 para memória de longo prazo.
    
    Inicializa a conexão com o provedor de memória (Supabase) e 
    fornece métodos para adicionar e buscar entradas de memória.
    """
    def __init__(self):
        """
        Inicializa o Mem0Manager e configura a instância Memory (síncrona).
        
        Tenta inicializar com Supabase se as configurações estiverem presentes,
        caso contrário, inicializa sem persistência.
        """
        # Volta a usar Memory (síncrona)
        self.mem0_instance: Optional[Memory] = None 
        self.is_configured: bool = False

        if settings.SUPABASE_CONNECTION_STRING:
            try:
                mem_config = {
                    "vector_store": {
                        "provider": "supabase",
                        "config": {
                            "connection_string": settings.SUPABASE_CONNECTION_STRING, 
                            "collection_name": "memories", 
                        }
                    },
                     # Configuração LLM (provavelmente ainda necessária)
                     "llm": { 
                         "provider": "openai", 
                         "config": {"api_key": settings.OPENAI_API_KEY}
                     } 
                }
                
                if not settings.OPENAI_API_KEY:
                     raise ValueError("OPENAI_API_KEY não configurada, necessária para Memory.")

                # Usa Memory.from_config() para inicializar
                self.mem0_instance = Memory.from_config(mem_config) 
                
                self.is_configured = True
                logger.info("Memory (síncrona) inicializada com sucesso usando Supabase (via from_config).")
                
            except ImportError as e:
                 logger.error(f"Erro ao importar dependências para Memory/Supabase: {e}. Verifique se 'mem0'/'mem0ai' e 'psycopg2-binary' estão instalados.")
                 self.is_configured = False
            except ValueError as e:
                 logger.error(f"Erro de configuração do Memory: {e}")
                 self.is_configured = False
            except Exception as e:
                logger.error(f"Erro ao inicializar Memory com Supabase: {e}", exc_info=True)
                self.is_configured = False
        else:
            logger.warning("Variável SUPABASE_CONNECTION_STRING não configurada. Memory será inicializado sem persistência Supabase.")
            # Inicialização padrão do Memory (sem Supabase)
            try:
                 if not settings.OPENAI_API_KEY:
                     raise ValueError("OPENAI_API_KEY não configurada, necessária para Memory padrão.")
                     
                 # Configuração mínima para Memory síncrona
                 # Pode precisar apenas da api_key se não usar from_config
                 self.mem0_instance = Memory(api_key=settings.OPENAI_API_KEY) 
                 logger.info("Memory (síncrona) inicializada sem persistência Supabase.")
                 
            except ValueError as e:
                 logger.error(f"Erro de configuração do Memory (padrão): {e}")
                 self.is_configured = False
            except Exception as e:
                 logger.error(f"Erro ao inicializar Memory (padrão): {e}", exc_info=True)
                 self.is_configured = False


    async def add_memory_entry(self, content: str, metadata: Optional[Dict[str, Any]] = None, agent_id: str = "voxy_brain") -> bool:
        """
        Adiciona uma nova entrada de memória usando Memory.add (síncrono),
        obtendo o user_id do contexto.
        """
        if self.mem0_instance is None: 
            logger.error("Instância Memory não foi criada. Não é possível adicionar memória.")
            return False
            
        # Obter user_id do contextvar
        user_id = current_user_id_var.get()
        if user_id is None:
            logger.error("Não foi possível obter o user_id do contexto. Abortando add_memory_entry.")
            return False
            
        try:
            # Reintroduz run_in_executor e partial
            loop = asyncio.get_running_loop()
            logger.debug(f"Adicionando memória via Memory.add para user_id='{user_id}', agent_id='{agent_id}': {content[:50]}...")
            
            # Não precisa mais da lista de mensagens, Memory.add pega o content direto
            add_partial = functools.partial(
                self.mem0_instance.add,
                content, # Passa o content diretamente
                user_id=str(user_id), # Garante que seja string para mem0
                agent_id=agent_id, # Memory síncrona suporta agent_id?
                metadata=metadata
            )
            
            result = await loop.run_in_executor(None, add_partial)
            
            logger.info(f"Entrada de memória adicionada via Memory.add: {str(result)}")
            return True 
        except Exception as e:
            logger.exception(f"Erro ao adicionar entrada de memória via Memory.add: {e}", exc_info=True)
            return False

    async def search_memory_entries(self, query: str, agent_id: str = "voxy_brain", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Busca entradas de memória relevantes usando Memory.search (síncrono),
        obtendo o user_id do contexto.
        """
        if self.mem0_instance is None:
            logger.error("Instância Memory não foi criada. Não é possível buscar memória.")
            return []
            
        # Obter user_id do contextvar
        user_id = current_user_id_var.get()
        if user_id is None:
            logger.error("Não foi possível obter o user_id do contexto. Abortando search_memory_entries.")
            return []
            
        try:
            # Reintroduz run_in_executor e partial
            loop = asyncio.get_running_loop()
            logger.debug(f"Buscando memória via Memory.search para user_id='{user_id}', agent_id='{agent_id}' com query: {query[:50]}...")
            
            search_partial = functools.partial(
                self.mem0_instance.search,
                query, 
                user_id=str(user_id), # Garante que seja string para mem0
                agent_id=agent_id, # Memory síncrona suporta agent_id?
                limit=limit
                # Remover output_format="v1.1" ?
            )
            
            results = await loop.run_in_executor(None, search_partial)

            # Assumindo que Memory.search retorna diretamente a lista
            logger.info(f"Busca de memória (Memory.search) retornou {len(results)} resultados para a query.")
            logger.debug(f"Resultados da busca: {results}") 
            return results if results else [] # Retorna lista vazia se for None/vazio
        except Exception as e:
            logger.exception(f"Erro ao buscar entradas de memória via Memory.search: {e}", exc_info=True)
            return []

# --- Padrões de Instanciação --- 

# Opção 1: Instância Singleton global
mem0_manager_instance: Optional[Mem0Manager] = None

def get_mem0_manager() -> Mem0Manager:
    """ Retorna a instância singleton do Mem0Manager, criando-a se necessário. """
    global mem0_manager_instance
    if mem0_manager_instance is None:
        logger.info("Criando instância singleton do Mem0Manager (usando Memory síncrona)...")
        mem0_manager_instance = Mem0Manager()
    return mem0_manager_instance

# Opção 2: Injeção de Dependência (comentada)

# Por agora, vamos usar a Opção 1 (Singleton via get_mem0_manager) para simplicidade. 