import asyncio
import logging
import contextvars
# Adicionar importação de typing
import typing
from typing import List, Dict, Any, Optional

# Importar MemoryConfig
from mem0.configs.base import MemoryConfig
# Mover AsyncMemory para TYPE_CHECKING
if typing.TYPE_CHECKING:
    from mem0.memory.main import AsyncMemory

from ..core.config import settings
from ..core.exceptions import BaseAppError # Importar exceção base

# Adicionar a definição do logger
logger = logging.getLogger(__name__)

# Definir o ContextVar para o user_id atual
current_user_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "current_user_id", default=None
)

class Mem0Manager:
    """
    Gerencia a interação com a biblioteca mem0 usando a interface AsyncMemory.
    
    Inicializa a conexão com o provedor de memória (Supabase) de forma assíncrona e 
    fornece métodos assíncronos para adicionar e buscar entradas de memória.
    """
    def __init__(self):
        """
        Inicializa o Mem0Manager e configura a instância AsyncMemory.
        
        Tenta inicializar com Supabase se as configurações estiverem presentes.
        """
        self.mem0_instance: Optional['AsyncMemory'] = None # Usar string para evitar importação direta
        self.is_configured: bool = False

        if settings.SUPABASE_CONNECTION_STRING:
            try:
                # Usar MemoryConfig para configuração
                mem_config = MemoryConfig(
                    vector_store={
                        "provider": "supabase",
                        "config": {
                            "connection_string": settings.SUPABASE_CONNECTION_STRING,
                            "collection_name": "memories", 
                        }
                    },
                    llm={ 
                        "provider": "openai", 
                        "config": {"api_key": settings.OPENAI_API_KEY}
                    }
                )
                
                if not settings.OPENAI_API_KEY:
                    raise ValueError("OPENAI_API_KEY não configurada, necessária para AsyncMemory.")

                # Inicializa AsyncMemory com a configuração
                # Adicionar importação dentro do try para evitar ciclo
                from mem0.memory.main import AsyncMemory
                self.mem0_instance = AsyncMemory(config=mem_config)
                
                self.is_configured = True
                logger.info("AsyncMemory inicializada com sucesso usando Supabase.")
                
            except ImportError as e:
                 logger.error(f"Erro ao importar dependências para AsyncMemory/Supabase: {e}. Verifique se 'mem0' e 'psycopg2-binary' estão instalados.")
                 self.is_configured = False
            except ValueError as e:
                 logger.error(f"Erro de configuração do AsyncMemory: {e}")
                 self.is_configured = False
            except Exception as e:
                logger.error(f"Erro ao inicializar AsyncMemory com Supabase: {e}", exc_info=True)
                self.is_configured = False
        else:
            logger.warning("Variável SUPABASE_CONNECTION_STRING não configurada. AsyncMemory não pôde ser configurado com persistência Supabase.")
            self.is_configured = False
            # Não inicializamos uma instância AsyncMemory sem persistência, pois a config é obrigatória.


    async def add_memory_entry(self, content: str, metadata: Optional[Dict[str, Any]] = None, agent_id: str = "voxy_brain") -> bool:
        """
        Adiciona uma nova entrada de memória usando AsyncMemory.add,
        obtendo o user_id do contexto.
        """
        if not self.is_configured or self.mem0_instance is None:
            logger.error("Instância AsyncMemory não foi configurada. Não é possível adicionar memória.")
            return False
            
        user_id = current_user_id_var.get()
        if user_id is None:
            logger.error("Não foi possível obter o user_id do contexto. Abortando add_memory_entry.")
            return False
            
        try:
            logger.debug(f"Adicionando memória via AsyncMemory.add para user_id='{user_id}', agent_id='{agent_id}': {content[:50]}...")
            
            # Chama diretamente o método assíncrono
            # Nota: AsyncMemory.add espera 'messages' como lista de dicts, não 'content' direto.
            # Adaptaremos isso nas ferramentas que chamam este método.
            # Aqui, vamos manter a assinatura, mas a chamada real pode precisar de ajuste.
            # ---> AJUSTE TEMPORÁRIO: Criando estrutura de mensagem mínima
            messages_input = [{"role": "user", "content": content}] # Simplificação!
            
            result = await self.mem0_instance.add(
                messages=messages_input, # Passa a lista de mensagens
                user_id=str(user_id), 
                agent_id=agent_id, 
                metadata=metadata
            )
            
            logger.info(f"Entrada de memória adicionada via AsyncMemory.add (Resultado: {str(result)})")
            # Assumir sucesso se não houver exceção, como antes.
            return True 
        except Exception as e:
            logger.exception(f"Erro ao adicionar memória via AsyncMemory.add para user_id='{user_id}': {e}", exc_info=True)
            # Levantar erro customizado pode ser útil aqui
            # raise BaseAppError(f"Falha ao adicionar memória: {e}")
            return False

    async def search_memory_entries(self, query: str, agent_id: str = "voxy_brain", limit: int = 5) -> List[Dict[str, Any]]:
        """
        Busca entradas de memória relevantes usando AsyncMemory.search,
        obtendo o user_id do contexto.
        """
        if not self.is_configured or self.mem0_instance is None:
            logger.error("Instância AsyncMemory não foi configurada. Não é possível buscar memória.")
            return []
            
        user_id = current_user_id_var.get()
        if user_id is None:
            logger.error("Não foi possível obter o user_id do contexto. Abortando search_memory_entries.")
            return []
            
        try:
            logger.debug(f"Buscando memória via AsyncMemory.search para user_id='{user_id}', agent_id='{agent_id}' com query: {query[:50]}...")
            
            # Chama diretamente o método assíncrono
            # Verificar se agent_id é suportado por AsyncMemory.search
            search_result = await self.mem0_instance.search(
                query=query,
                user_id=str(user_id),
                agent_id=agent_id, # Confirmar suporte
                limit=limit
            )

            # O método search retorna um dict com uma chave 'results'
            results = search_result.get("results", [])
            logger.info(f"Busca de memória (AsyncMemory.search) retornou {len(results)} resultados para a query.")
            logger.debug(f"Resultados da busca: {results}") 
            return results if results else []
        except Exception as e:
            logger.exception(f"Erro ao buscar entradas de memória via AsyncMemory.search: {e}", exc_info=True)
            return []

    async def get_all_memory_entries(self, agent_id: str = "voxy_brain") -> List[Dict[str, Any]]:
        """
        Busca todas as entradas de memória de um usuário usando AsyncMemory.get_all,
        obtendo o user_id do contexto.
        """
        if not self.is_configured or self.mem0_instance is None:
            logger.error("Instância AsyncMemory não foi configurada. Não é possível buscar todas as memórias.")
            return []

        user_id = current_user_id_var.get()
        if user_id is None:
            logger.error("Não foi possível obter o user_id do contexto. Abortando get_all_memory_entries.")
            return []

        try:
            logger.debug(f"Buscando TODAS as memórias via AsyncMemory.get_all para user_id='{user_id}', agent_id='{agent_id}'...")

            # Chama diretamente o método assíncrono
            # Verificar se agent_id é suportado por AsyncMemory.get_all
            results = await self.mem0_instance.get_all(
                user_id=str(user_id)
                # agent_id=agent_id # Confirmar suporte
            )

            logger.info(f"Busca de TODAS as memórias (AsyncMemory.get_all) retornou {len(results)} resultados.")
            logger.debug(f"Resultados da busca get_all: {results}")
            return results if results else []
        except Exception as e:
            logger.exception(f"Erro ao buscar todas as entradas de memória via AsyncMemory.get_all: {e}", exc_info=True)
            return []

# --- Padrões de Instanciação --- 

# Instância Singleton global (agora usando AsyncMemory)
mem0_manager_instance: Optional[Mem0Manager] = None

def get_mem0_manager() -> Mem0Manager:
    """ Retorna a instância singleton do Mem0Manager, criando-a se necessário. """
    global mem0_manager_instance
    if mem0_manager_instance is None:
        logger.info("Criando instância singleton do Mem0Manager (usando AsyncMemory)...")
        mem0_manager_instance = Mem0Manager()
        if not mem0_manager_instance.is_configured:
            # Log adicional se a configuração falhar na criação do singleton
            logger.error("Falha ao configurar o Mem0Manager singleton. A memória não estará funcional.")
    return mem0_manager_instance 