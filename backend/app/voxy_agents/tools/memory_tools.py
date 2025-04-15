# backend/app/voxy_agents/tools/memory_tools.py
import logging
import traceback
import typing
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

# Importa o decorator de ferramenta
from agents import function_tool

# Mover importação para TYPE_CHECKING
if typing.TYPE_CHECKING:
    from mem0.memory.main import AsyncMemory # Importar se for usar type hints

# Importar o gerenciador de memória assíncrono
from app.memory.mem0_manager import get_mem0_manager, Mem0Manager

logger = logging.getLogger(__name__)

# Modelo Pydantic para os metadados da memória
class MemoryMetadata(BaseModel):
    """Define a estrutura esperada para os metadados da memória."""
    tipo: str
    categoria: str
    valor: Optional[str] = None
    sentimento: Optional[str] = None

@function_tool
async def remember_info(information: str, metadata: MemoryMetadata) -> str:
    """
    Memoriza uma informação textual concisa (`information`) associando-a a 
    metadados estruturados (`metadata`). O ID do usuário é obtido do contexto.
    
    Use para salvar fatos chave, preferências, tarefas ou inferências.
    Forneça `metadata` compatível com MemoryMetadata (requer `tipo` e `categoria`).
    **Evite salvar detalhes triviais.**

    Args:
        information (str): A informação textual concisa a ser memorizada.
        metadata (MemoryMetadata): Metadados estruturados (requer `tipo`, `categoria`).

    Returns:
        str: Uma mensagem de confirmação ou erro.
    """
    logger.debug(f"[MEMORY TOOL ASYNC] Entrando em remember_info: '{information[:50]}...', {metadata}")
    mem0_manager: Mem0Manager = get_mem0_manager()
    agent_id = "voxy_brain"

    if not mem0_manager.is_configured:
        logger.error("[MEMORY TOOL ASYNC] Mem0 não configurado. Abortando remember_info.")
        return "Desculpe, não consigo memorizar (configuração)."

    try:
        metadata_dict = metadata.model_dump(exclude_unset=True)
        logger.debug(f"[MEMORY TOOL ASYNC] Chamando mem0_manager.add_memory_entry...")
        
        # Ajuste: Passar a informação como parte de uma lista de mensagens
        # O manager agora espera a estrutura de `messages` para AsyncMemory.add
        # Vamos criar uma mensagem mínima de "usuário" para encapsular a informação.
        # Isso pode precisar de refinamento se o LLM fornecer um histórico melhor.
        messages_for_memory = [{
            "role": "user", # Assumindo que a info veio do usuário ou inferida
            "content": information
        }]

        # Chamada direta ao método assíncrono do manager
        success = await mem0_manager.add_memory_entry(
            content=information, # O manager agora ignora isso e usa messages_for_memory
                                 # TODO: Refatorar a assinatura de add_memory_entry no manager
                                 #       para aceitar `messages` em vez de `content`.
                                 #       Por agora, passamos ambos, mas o manager usa o formato interno.
            metadata=metadata_dict,
            agent_id=agent_id
            # O manager internamente usará messages_for_memory
        )
        logger.debug(f"[MEMORY TOOL ASYNC] add_memory_entry retornou: {success}")

        if success:
            categoria = metadata.categoria
            logger.info(f"Informação sobre '{categoria}' memorizada com sucesso (async).")
            return f"Ok, memorizei a informação sobre '{categoria}'."
        else:
            logger.error("[MEMORY TOOL ASYNC] Falha ao memorizar (retorno False).")
            return "Desculpe, erro interno ao memorizar."

    except Exception as e:
        logger.error(f"[MEMORY TOOL ASYNC] Exceção em remember_info: {e}\n{traceback.format_exc()}")
        return "Desculpe, erro inesperado ao memorizar."


@function_tool
async def recall_info(query: str, limit: Optional[int] = None) -> str:
    """
    Busca na memória informações relevantes para a `query` associadas ao usuário atual.
    Foca em busca semântica.

    Args:
        query (str): A pergunta ou tópico para busca.
        limit (Optional[int]): Número máximo de resultados (padrão: 3).

    Returns:
        str: Informações encontradas ou mensagem de erro/não encontrado.
    """
    actual_limit = limit if limit is not None and limit > 0 else 3
    logger.debug(f"[MEMORY TOOL ASYNC] recall_info: Query='{query[:50]}...', Limite={actual_limit}")
    mem0_manager: Mem0Manager = get_mem0_manager()
    agent_id = "voxy_brain"

    if not mem0_manager.is_configured:
        logger.error("[MEMORY TOOL ASYNC] Mem0 não configurado. Abortando recall_info.")
        return "Desculpe, não consigo buscar na memória (configuração)."

    try:
        logger.debug(f"[MEMORY TOOL ASYNC] Chamando mem0_manager.search_memory_entries...")
        # Chamada direta ao método assíncrono
        results = await mem0_manager.search_memory_entries(
            query=query,
            limit=actual_limit,
            agent_id=agent_id
        )
        # O manager agora retorna a lista diretamente

        if not results:
            logger.info(f"[MEMORY TOOL ASYNC] Nenhuma info relevante para query: '{query}'.")
            return f"Não encontrei nada na memória sobre '{query}'."
        else:
            logger.info(f"[MEMORY TOOL ASYNC] {len(results)} infos relevantes para query: '{query}'.")
            formatted_results = []
            for i, memory_item in enumerate(results):
                memory_text = memory_item.get('memory', memory_item.get('text', str(memory_item)))
                formatted_results.append(f"{i+1}. {memory_text}")

            logger.debug(f"[MEMORY TOOL ASYNC] Resultados formatados: {formatted_results}")
            return "Encontrei o seguinte na memória:\n" + "\n".join(formatted_results)

    except Exception as e:
        logger.error(f"[MEMORY TOOL ASYNC] Erro inesperado em recall_info: {e}\n{traceback.format_exc()}")
        return "Desculpe, erro inesperado ao buscar na memória."


@function_tool
async def summarize_memory() -> str:
    """
    Busca *todas* as memórias associadas ao usuário atual e retorna um resumo.
    Use quando perguntado abertamente (ex: "O que você lembra?").

    Returns:
        str: Resumo das memórias ou mensagem de erro/não encontrado.
    """
    logger.debug("[MEMORY TOOL ASYNC] summarize_memory chamada.")
    mem0_manager: Mem0Manager = get_mem0_manager()
    agent_id = "voxy_brain"

    if not mem0_manager.is_configured:
        logger.error("[MEMORY TOOL ASYNC] Mem0 não configurado. Abortando summarize_memory.")
        return "Desculpe, não consigo acessar a memória (configuração)."

    try:
        logger.debug(f"[MEMORY TOOL ASYNC] Chamando mem0_manager.get_all_memory_entries...")
        # Chamada direta ao método assíncrono
        all_memories = await mem0_manager.get_all_memory_entries(agent_id=agent_id)
        # O manager agora retorna a lista diretamente

        if not all_memories:
            logger.info("[MEMORY TOOL ASYNC] Nenhuma memória encontrada para resumir.")
            return "Não encontrei memórias registradas."
        else:
            logger.info(f"[MEMORY TOOL ASYNC] {len(all_memories)} memórias encontradas para resumir.")
            summaries: Dict[str, List[str]] = {
                "preferência": [], "fato_pessoal": [], "lembrete": [],
                "inferência": [], "outros": []
            }
            processed_count = 0
            for memory in all_memories:
                metadata = memory.get('metadata', {})
                text = memory.get('memory', memory.get('text', None))
                if text and isinstance(metadata, dict):
                    category_key = metadata.get('tipo', 'outros')
                    if category_key not in summaries: category_key = 'outros'
                    summaries[category_key].append(text)
                    processed_count += 1
                else:
                    logger.warning(f"[MEMORY TOOL ASYNC] Memória ignorada: {memory}")

            if processed_count == 0:
                 logger.info("[MEMORY TOOL ASYNC] Nenhuma memória válida após processamento.")
                 return "Não encontrei memórias válidas para resumir."

            output_lines = ["Resumo do que lembro sobre você:"]
            category_map = {
                "preferência": "Preferências", "fato_pessoal": "Fatos Pessoais",
                "lembrete": "Lembretes/Tarefas", "inferência": "Observações",
                "outros": "Outros"
            }
            for category_key, items in summaries.items():
                if items:
                    title = category_map.get(category_key, category_key.replace('_', ' ').title())
                    output_lines.append(f"\n**{title}:**")
                    output_lines.extend([f"- {item}" for item in items])

            final_summary = "\n".join(output_lines)
            logger.debug(f"[MEMORY TOOL ASYNC] Resumo gerado: {final_summary[:200]}...")
            return final_summary

    except Exception as e:
        logger.error(f"[MEMORY TOOL ASYNC] Erro inesperado em summarize_memory: {e}\n{traceback.format_exc()}")
        return "Desculpe, erro inesperado ao resumir a memória." 