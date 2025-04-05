# backend/app/agents/tools/memory_tools.py
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel # Importar BaseModel

# Importa o decorator de ferramenta e o gerenciador de memória
from agents import function_tool 
# Usamos a função get_mem0_manager para obter a instância Singleton
# TENTATIVA: Mudar para import absoluto baseado em 'app' para pytest
from app.memory.mem0_manager import get_mem0_manager

logger = logging.getLogger(__name__)

# Definir um modelo Pydantic para metadados
class MetadataModel(BaseModel):
    """ Modelo para metadados opcionais associados a uma memória. """
    source: Optional[str] = None
    # Adicione outros campos conforme necessário
    # Exemplo: timestamp: Optional[datetime] = None

@function_tool
async def remember_info(content: str, metadata: Optional[MetadataModel] = None) -> str:
    """
    Memoriza uma informação específica fornecida pelo usuário ou identificada como 
    importante durante a conversa para referência futura, vinculando-a ao ID do 
    usuário atual (obtido automaticamente do contexto).

    Use esta ferramenta para salvar fatos chave, preferências ou detalhes 
    significativos sobre o usuário atual que podem ser úteis em interações futuras. 
    Isso pode ser acionado por um pedido explícito do usuário ('lembre-se', 'anote') 
    ou por sua própria iniciativa ao identificar informações valiosas. 
    **Evite salvar detalhes triviais ou efêmeros da conversa.**

    Args:
        content (str): A informação exata que deve ser memorizada. Seja o mais 
                       completo possível.
        metadata (Optional[MetadataModel]): Metadados opcionais estruturados 
                                              (ex: {"source": "user_preference"}).

    Returns:
        str: Uma mensagem de confirmação indicando se a informação foi memorizada com sucesso ou não.
    """
    logger.debug(f"'remember_info' chamada. Conteúdo: '{content[:50]}...', Metadata: {metadata}")
    mem0_manager = get_mem0_manager()
    
    # user_id agora é obtido pelo Mem0Manager do contextvar
    agent_id = "voxy_brain"

    if not mem0_manager.is_configured and mem0_manager.mem0_instance is None:
         logger.error("Mem0 não está configurado ou inicializado. Não é possível usar remember_info.")
         # Retorna mensagem de erro clara para o LLM
         return "Desculpe, não consigo memorizar informações no momento devido a um problema de configuração da memória."

    # Converte o modelo Pydantic para dict antes de passar para o manager
    metadata_dict = metadata.model_dump(exclude_unset=True) if metadata else None
    logger.debug(f"Metadados convertidos para dict: {metadata_dict}")

    success = await mem0_manager.add_memory_entry(
        content=content, 
        metadata=metadata_dict, # Passa o dicionário
        agent_id=agent_id
    )

    if success:
        logger.info("Informação memorizada com sucesso.")
        # Retorna confirmação clara para o LLM/usuário
        return f"Ok, memorizei: '{content[:100]}...'" 
    else:
        logger.error("Falha ao tentar memorizar a informação.")
        # Retorna mensagem de erro clara para o LLM
        return "Desculpe, ocorreu um erro e não consegui memorizar a informação."


@function_tool
async def recall_info(query: str, limit: Optional[int] = None) -> str:
    """
    Busca na memória informações previamente memorizadas pelo usuário atual
    (obtido automaticamente do contexto) que sejam relevantes para a consulta.

    Use esta ferramenta proativamente para verificar se há contexto relevante 
    armazenado sobre um tópico antes de responder, ou quando o usuário perguntar 
    explicitamente sobre algo passado (ex: 'qual era meu restaurante favorito?', 
    'o que você sabe sobre X que eu te disse?'). Integrar as informações 
    recuperadas pode personalizar significativamente a resposta.

    Args:
        query (str): A pergunta, tópico ou palavras-chave sobre o qual buscar 
                     informações na memória. Seja específico para obter melhores resultados.
        limit (Optional[int]): O número máximo de memórias relevantes a serem retornadas.
                             Se não fornecido, o padrão interno será 3.

    Returns:
        str: Uma string contendo as informações encontradas na memória que correspondem 
             à consulta, formatadas para fácil leitura. Se nada for encontrado, 
             indicará isso. Em caso de erro, informará sobre o problema.
    """
    # Define o valor padrão internamente se não for fornecido
    actual_limit = limit if limit is not None and limit > 0 else 3
    logger.debug(f"'recall_info' chamada. Query: '{query[:50]}...', Limit fornecido: {limit}, Limite a usar: {actual_limit}")
    mem0_manager = get_mem0_manager()

    # user_id agora é obtido pelo Mem0Manager do contextvar
    agent_id = "voxy_brain"
    
    if not mem0_manager.is_configured and mem0_manager.mem0_instance is None:
         logger.error("Mem0 não está configurado ou inicializado. Não é possível usar recall_info.")
         return "Desculpe, não consigo buscar informações na memória no momento devido a um problema de configuração."

    logger.debug(f"Chamando mem0_manager.search_memory_entries com query: '{query}', limit: {actual_limit}")
    results = await mem0_manager.search_memory_entries(
        query=query, 
        limit=actual_limit, # Usa o limite real
        agent_id=agent_id
    )

    if not results:
        logger.debug("Nenhum resultado encontrado na busca de memória.")
        logger.info("Nenhuma informação relevante encontrada na memória.")
        return f"Não encontrei nenhuma informação na memória sobre '{query}'."
    else:
        logger.info(f"Encontradas {len(results)} informações relevantes na memória.")
        # Formata os resultados para o LLM/usuário
        # A estrutura exata de cada 'result' em 'results' depende do mem0ai
        formatted_results = []
        for i, result in enumerate(results):
            # Tenta extrair o texto da memória, pode precisar ajustar a chave ('text', 'content', 'memory', etc.)
            # A chave 'memory' parece ser comum nos exemplos do mem0ai
            memory_text = result.get('memory', result.get('text', str(result))) 
            formatted_results.append(f"{i+1}. {memory_text}") 
            
        logger.debug(f"Resultados formatados: {formatted_results}")
        return "Encontrei as seguintes informações na memória sobre sua consulta:\n" + "\n".join(formatted_results) 