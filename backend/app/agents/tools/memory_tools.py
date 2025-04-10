# backend/app/agents/tools/memory_tools.py
import logging
import asyncio
import traceback
from typing import List, Dict, Any, Optional
from pydantic import BaseModel # Importar BaseModel

# Importa o decorator de ferramenta e o gerenciador de memória
from agents import function_tool 
# Usamos a função get_mem0_manager para obter a instância Singleton
# TENTATIVA: Mudar para import absoluto baseado em 'app' para pytest
from app.memory.mem0_manager import get_mem0_manager, Mem0Manager # Importar Mem0Manager para type hint

logger = logging.getLogger(__name__)

# Modelo Pydantic para os metadados da memória - Reintroduzido para schema estrito
class MemoryMetadata(BaseModel):
    """Define a estrutura esperada para os metadados da memória."""
    tipo: str  # Ex: "preferência", "fato_pessoal", "lembrete", "inferência"
    categoria: str # Ex: "alimentação", "comunicação", "trabalho", "animal_estimação"
    # Adicionar outros campos comuns como opcionais, se necessário
    valor: Optional[str] = None
    sentimento: Optional[str] = None
    # Permite campos extras sem falhar na validação inicial, mas não serão usados no schema principal
    # Configuração de Pydantic para permitir campos extras sem erro, se necessário.
    # class Config:
    #     extra = 'allow'

@function_tool
async def remember_info(information: str, metadata: MemoryMetadata) -> str:
    """
    Memoriza uma informação textual concisa (`information`) fornecida pelo usuário
    ou identificada como importante, associando-a a metadados estruturados
    (`metadata`) para referência futura. O ID do usuário atual é obtido
    automaticamente do contexto.

    Use esta ferramenta para salvar fatos chave, preferências explícitas, tarefas,
    lembretes ou inferências de alta confiança sobre o usuário atual. Forneça a
    `information` como uma string clara e os `metadata` como um objeto JSON
    compatível com o schema MemoryMetadata (requer `tipo` e `categoria`).

    **Evite salvar detalhes triviais ou efêmeros.**

    Exemplo de Chamada (pelo LLM):
    `remember_info(information="Não gosto de queijo", metadata={"tipo": "preferência", "categoria": "alimentação", "valor": "queijo", "sentimento": "negativo"})`

    Args:
        information (str): A informação textual concisa que deve ser memorizada.
        metadata (MemoryMetadata): Metadados estruturados obrigatórios descrevendo
                                   a informação (requer `tipo` e `categoria`).

    Returns:
        str: Uma mensagem de confirmação ou erro.
    """
    logger.debug(f"[MEMORY TOOL] Entrando em remember_info. Informação: '{information[:50]}...', Metadata: {metadata}")
    mem0_manager: Mem0Manager = get_mem0_manager()
    agent_id = "voxy_brain" # Pode ser configurável se necessário
    logger.debug(f"[MEMORY TOOL] Instância Mem0Manager obtida: {mem0_manager}")

    if not mem0_manager.is_configured:
        logger.error("[MEMORY TOOL] Mem0 não está configurado. Abortando remember_info.")
        return "Desculpe, não consigo memorizar informações no momento (problema de configuração)."
    logger.debug(f"[MEMORY TOOL] Verificação de configuração do Mem0Manager passou.")

    # Validação Pydantic ocorre automaticamente na assinatura da função agora

    try:
        logger.debug(f"[MEMORY TOOL] Tentando converter metadados Pydantic para dict...")
        # Converte o modelo Pydantic para dict antes de passar para o manager
        # Usar exclude_unset=True para não enviar campos opcionais não definidos
        metadata_dict = metadata.model_dump(exclude_unset=True)
        logger.debug(f"[MEMORY TOOL] Metadados convertidos para dict: {metadata_dict}")

        # Assumindo que add_memory_entry lida com contextvar e asyncio.to_thread se necessário
        logger.debug(f"[MEMORY TOOL] Chamando mem0_manager.add_memory_entry...")
        success = await mem0_manager.add_memory_entry(
            content=information,
            metadata=metadata_dict, # Passa o dicionário
            agent_id=agent_id
        )
        logger.debug(f"[MEMORY TOOL] Chamada a add_memory_entry retornou: {success}")

        if success:
            categoria = metadata.categoria # Acessa diretamente o atributo do modelo
            logger.info(f"Informação sobre '{categoria}' memorizada com sucesso.")
            return f"Ok, memorizei a informação sobre '{categoria}'."
        else:
            logger.error("[MEMORY TOOL] Falha ao tentar memorizar a informação (retorno False do manager).")
            return "Desculpe, ocorreu um erro interno e não consegui memorizar a informação."

    except Exception as e:
        logger.error(f"[MEMORY TOOL] Exceção capturada em remember_info: {e}\n{traceback.format_exc()}")
        return "Desculpe, ocorreu um erro inesperado ao tentar memorizar a informação."


@function_tool
async def recall_info(query: str, limit: Optional[int] = None) -> str:
    """
    Busca na memória informações relevantes para a `query` associadas ao usuário
    atual (obtido automaticamente do contexto). Foca em busca semântica.

    Use esta ferramenta proativamente para verificar contexto relevante armazenado
    antes de responder, ou quando o usuário perguntar sobre algo específico que foi
    dito anteriormente. Contrasta com `summarize_memory` que busca *todas* as memórias.

    Args:
        query (str): A pergunta, tópico ou palavras-chave para a busca semântica.
        limit (Optional[int]): O número máximo de memórias relevantes (padrão: 3).

    Returns:
        str: Informações encontradas formatadas, ou uma mensagem indicando que nada
             foi encontrado ou que ocorreu um erro.
    """
    actual_limit = limit if limit is not None and limit > 0 else 3
    logger.debug(f"'recall_info' chamada. Query: '{query[:50]}...', Limite: {actual_limit}")
    mem0_manager: Mem0Manager = get_mem0_manager()
    agent_id = "voxy_brain"

    if not mem0_manager.is_configured:
        logger.error("Mem0 não está configurado. Não é possível usar recall_info.")
        return "Desculpe, não consigo buscar na memória no momento (problema de configuração)."

    try:
        # Assumindo que search_memory_entries lida com contextvar e asyncio.to_thread
        logger.debug(f"Chamando mem0_manager.search_memory_entries com query: '{query}', limit: {actual_limit}")
        results = await mem0_manager.search_memory_entries(
            query=query,
            limit=actual_limit,
            agent_id=agent_id
        )

        if not results:
            logger.info(f"Nenhuma informação relevante encontrada na memória para query: '{query}'.")
            return f"Não encontrei nenhuma informação na memória sobre '{query}'."
        else:
            logger.info(f"Encontradas {len(results.get('results', []))} informações relevantes na memória para query: '{query}'.")
            formatted_results = []
            # Corrigir o loop para iterar sobre a lista dentro da chave 'results'
            memory_list = results.get('results', []) # Pega a lista ou uma lista vazia se a chave não existir
            for i, memory_item in enumerate(memory_list):
                # A chave 'memory' parece ser a padrão retornada pelo mem0 search
                # Agora 'memory_item' é o dicionário da memória individual
                memory_text = memory_item.get('memory', memory_item.get('text', str(memory_item)))
                formatted_results.append(f"{i+1}. {memory_text}")

            logger.debug(f"Resultados formatados para recall_info: {formatted_results}")
            return "Encontrei as seguintes informações relevantes na memória:\n" + "\n".join(formatted_results)

    except Exception as e:
        logger.error(f"Erro inesperado ao tentar buscar na memória: {e}\n{traceback.format_exc()}")
        return "Desculpe, ocorreu um erro inesperado ao tentar buscar na memória."


@function_tool
async def summarize_memory() -> str:
    """
    Busca *todas* as memórias associadas ao usuário atual (obtido do contexto),
    categoriza-as com base nos metadados e retorna um resumo formatado.

    Use esta ferramenta quando o usuário perguntar abertamente sobre o que você
    lembra sobre ele (ex: "O que você sabe sobre mim?", "Resuma nossa interação").

    Returns:
        str: Um resumo das memórias categorizadas ou uma mensagem indicando que
             não há memórias ou que ocorreu um erro.
    """
    logger.debug("'summarize_memory' chamada.")
    mem0_manager: Mem0Manager = get_mem0_manager()
    agent_id = "voxy_brain"

    if not mem0_manager.is_configured:
        logger.error("Mem0 não está configurado. Não é possível usar summarize_memory.")
        return "Desculpe, não consigo acessar a memória no momento (problema de configuração)."

    try:
        # Assumindo que Mem0Manager tem get_all_memories que usa contextvar e asyncio.to_thread
        logger.debug(f"Chamando mem0_manager.get_all_memory_entries para o agent_id: {agent_id}")
        all_memories = await mem0_manager.get_all_memory_entries(agent_id=agent_id)

        if not all_memories:
            logger.info("Nenhuma memória encontrada para resumir.")
            return "Não encontrei nenhuma memória registrada para você ainda."
        else:
            logger.info(f"Encontradas {len(all_memories)} memórias para resumir.")
            # Processar e categorizar resultados
            summaries: Dict[str, List[str]] = {
                "preferência": [],
                "fato_pessoal": [],
                "lembrete": [],
                "inferência": [],
                "outros": []
            }
            
            processed_count = 0
            for memory in all_memories:
                metadata = memory.get('metadata', {})
                text = memory.get('memory', memory.get('text', None))
                
                if text and isinstance(metadata, dict):
                    category_key = metadata.get('tipo', 'outros') # Usar 'tipo' para categorizar
                    if category_key not in summaries:
                        category_key = 'outros' # Coloca em 'outros' se tipo não for conhecido
                    summaries[category_key].append(text)
                    processed_count += 1
                else:
                     logger.warning(f"Memória ignorada por falta de texto ou metadados inválidos: {memory}")

            if processed_count == 0:
                 logger.info("Nenhuma memória válida encontrada após processamento.")
                 return "Não encontrei nenhuma memória válida para resumir no momento."

            # Formatar a string de saída
            output_lines = ["Aqui está um resumo do que eu lembro sobre você:"]
            category_map = {
                "preferência": "Preferências",
                "fato_pessoal": "Fatos Pessoais",
                "lembrete": "Lembretes/Tarefas",
                "inferência": "Observações/Inferências",
                "outros": "Outros"
            }

            for category_key, items in summaries.items():
                if items:
                    title = category_map.get(category_key, category_key.replace('_', ' ').title())
                    output_lines.append(f"\n**{title}:**")
                    output_lines.extend([f"- {item}" for item in items])

            final_summary = "\n".join(output_lines)
            logger.debug(f"Resumo da memória gerado: {final_summary[:200]}...")
            return final_summary

    except AttributeError as e:
         # Captura especificamente se get_all_memories não existir no manager
         logger.error(f"Erro ao chamar get_all_memory_entries (método existe?): {e}\n{traceback.format_exc()}")
         return "Desculpe, ocorreu um erro ao tentar acessar a função de resumo da memória (possível método ausente)."
    except Exception as e:
        logger.error(f"Erro inesperado ao tentar resumir a memória: {e}\n{traceback.format_exc()}")
        return "Desculpe, ocorreu um erro inesperado ao tentar resumir a memória." 