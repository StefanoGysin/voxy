import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.voxy_agents.tools.memory_tools import (
    remember_info,
    recall_info,
    summarize_memory,
    MemoryMetadata,
)
from app.memory.mem0_manager import Mem0Manager # Importar a classe para mock

# Marcar todos os testes neste módulo para usar asyncio
pytestmark = pytest.mark.asyncio

# Extrair a função original por trás do decorador @function_tool
# Criar funções auxiliares para extrair a lógica das ferramentas decoradas
@patch('app.voxy_agents.tools.memory_tools.get_mem0_manager')
async def test_remember_info_success(mock_get_manager):
    """Teste de sucesso.""" # Minimal ASCII docstring
    # Configurar o mock do manager
    mock_manager = AsyncMock(spec=Mem0Manager)
    mock_manager.is_configured = True
    mock_manager.add_memory_entry = AsyncMock(return_value=True) # Simula sucesso
    mock_get_manager.return_value = mock_manager

    info = "Lembrar disso"
    metadata = MemoryMetadata(tipo="lembrete", categoria="teste")
    
    # Criar um contexto mock - necessário para invocar a ferramenta
    mock_context = MagicMock()
    
    # Invocando diretamente a função _on_invoke_tool da FunctionTool
    # Convertendo os argumentos para JSON, como o Runner faria
    import json
    args_json = json.dumps({
        "information": info,
        "metadata": metadata.model_dump()
    })
    
    # Chamar a função embutida na ferramenta
    result = await remember_info.on_invoke_tool(mock_context, args_json)

    # Verificar se o manager foi chamado corretamente
    mock_manager.add_memory_entry.assert_awaited_once()
    call_args, call_kwargs = mock_manager.add_memory_entry.call_args
    # Verificar se a informação e metadados foram passados corretamente
    assert call_kwargs['content'] == info
    assert call_kwargs['metadata'] == metadata.model_dump()
    assert call_kwargs['agent_id'] == "voxy_brain"

    # Verificar o resultado
    assert result == f"Ok, memorizei a informação sobre '{metadata.categoria}'."

@patch('app.voxy_agents.tools.memory_tools.get_mem0_manager')
async def test_remember_info_manager_not_configured(mock_get_manager):
    """Testa remember_info quando o manager não está configurado."""
    # Configurar o mock do manager para não estar configurado
    mock_manager = AsyncMock(spec=Mem0Manager)
    mock_manager.is_configured = False
    mock_get_manager.return_value = mock_manager

    info = "Info irrelevante"
    metadata = MemoryMetadata(tipo="tipo", categoria="categoria")
    
    # Criar um contexto mock - necessário para invocar a ferramenta
    mock_context = MagicMock()
    
    # Invocando diretamente a função _on_invoke_tool da FunctionTool
    # Convertendo os argumentos para JSON, como o Runner faria
    import json
    args_json = json.dumps({
        "information": info,
        "metadata": metadata.model_dump()
    })
    
    # Chamar a função embutida na ferramenta
    result = await remember_info.on_invoke_tool(mock_context, args_json)

    # Verificar que add_memory_entry não foi chamado
    mock_manager.add_memory_entry.assert_not_awaited()

    # Verificar a mensagem de erro
    assert result == "Desculpe, não consigo memorizar (configuração)."

@patch('app.voxy_agents.tools.memory_tools.get_mem0_manager')
async def test_remember_info_add_fails(mock_get_manager):
    """Testa remember_info quando add_memory_entry falha (retorna False)."""
    # Configurar o mock do manager para retornar False no add
    mock_manager = AsyncMock(spec=Mem0Manager)
    mock_manager.is_configured = True
    mock_manager.add_memory_entry = AsyncMock(return_value=False) # Simula falha
    mock_get_manager.return_value = mock_manager

    info = "Info que falhará"
    metadata = MemoryMetadata(tipo="tipo", categoria="falha")
    
    # Criar um contexto mock - necessário para invocar a ferramenta
    mock_context = MagicMock()
    
    # Invocando diretamente a função _on_invoke_tool da FunctionTool
    # Convertendo os argumentos para JSON, como o Runner faria
    import json
    args_json = json.dumps({
        "information": info,
        "metadata": metadata.model_dump()
    })
    
    # Chamar a função embutida na ferramenta
    result = await remember_info.on_invoke_tool(mock_context, args_json)

    # Verificar que add_memory_entry foi chamado
    mock_manager.add_memory_entry.assert_awaited_once()

    # Verificar a mensagem de erro
    assert result == "Desculpe, erro interno ao memorizar."

@patch('app.voxy_agents.tools.memory_tools.get_mem0_manager')
async def test_remember_info_exception(mock_get_manager):
    """Testa remember_info quando ocorre uma exceção inesperada."""
    # Configurar o mock do manager para levantar exceção
    mock_manager = AsyncMock(spec=Mem0Manager)
    mock_manager.is_configured = True
    mock_manager.add_memory_entry = AsyncMock(side_effect=Exception("Erro simulado"))
    mock_get_manager.return_value = mock_manager

    info = "Info com exceção"
    metadata = MemoryMetadata(tipo="tipo", categoria="excecao")
    
    # Criar um contexto mock - necessário para invocar a ferramenta
    mock_context = MagicMock()
    
    # Invocando diretamente a função _on_invoke_tool da FunctionTool
    # Convertendo os argumentos para JSON, como o Runner faria
    import json
    args_json = json.dumps({
        "information": info,
        "metadata": metadata.model_dump()
    })
    
    # Chamar a função embutida na ferramenta
    result = await remember_info.on_invoke_tool(mock_context, args_json)

    # Verificar que add_memory_entry foi chamado
    mock_manager.add_memory_entry.assert_awaited_once()

    # Verificar a mensagem de erro genérica
    assert result == "Desculpe, erro inesperado ao memorizar."

# --- Testes para recall_info ---

@patch('app.voxy_agents.tools.memory_tools.get_mem0_manager')
async def test_recall_info_success_default_limit(mock_get_manager):
    """Testa recall_info com sucesso usando o limite padrão (3)."""
    # Configurar o mock do manager para retornar resultados
    mock_manager = AsyncMock(spec=Mem0Manager)
    mock_manager.is_configured = True
    mock_results = [
        {"memory": "Resultado 1", "metadata": {}},
        {"text": "Resultado 2", "metadata": {}}, # Testar chave 'text' alternativa
        {"memory": "Resultado 3", "metadata": {}}
    ]
    mock_manager.search_memory_entries = AsyncMock(return_value=mock_results)
    mock_get_manager.return_value = mock_manager

    query = "Busca teste"
    
    # Criar um contexto mock - necessário para invocar a ferramenta
    mock_context = MagicMock()
    
    # Invocando diretamente a função _on_invoke_tool da FunctionTool
    # Convertendo os argumentos para JSON, como o Runner faria
    import json
    args_json = json.dumps({
        "query": query
    })
    
    # Chamar a função embutida na ferramenta
    result = await recall_info.on_invoke_tool(mock_context, args_json)

    # Verificar se search_memory_entries foi chamado com o limite padrão
    mock_manager.search_memory_entries.assert_awaited_once_with(
        query=query,
        limit=3, # Limite padrão
        agent_id="voxy_brain"
    )

    # Verificar o resultado formatado
    expected_result = (
        "Encontrei o seguinte na memória:\n"
        "1. Resultado 1\n"
        "2. Resultado 2\n"
        "3. Resultado 3"
    )
    assert result == expected_result

@patch('app.voxy_agents.tools.memory_tools.get_mem0_manager')
async def test_recall_info_success_custom_limit(mock_get_manager):
    """Testa recall_info com sucesso usando um limite customizado."""
    # Configurar o mock do manager para retornar 5 resultados
    mock_manager = AsyncMock(spec=Mem0Manager)
    mock_manager.is_configured = True
    mock_results = [
        {"memory": f"Item {i}", "metadata": {}} for i in range(1, 6)
    ]
    mock_manager.search_memory_entries = AsyncMock(return_value=mock_results)
    mock_get_manager.return_value = mock_manager

    query = "Busca customizada"
    custom_limit = 5
    
    # Criar um contexto mock - necessário para invocar a ferramenta
    mock_context = MagicMock()
    
    # Invocando diretamente a função _on_invoke_tool da FunctionTool
    # Convertendo os argumentos para JSON, como o Runner faria
    import json
    args_json = json.dumps({
        "query": query,
        "limit": custom_limit
    })
    
    # Chamar a função embutida na ferramenta
    result = await recall_info.on_invoke_tool(mock_context, args_json)

    # Verificar se search_memory_entries foi chamado com o limite customizado
    mock_manager.search_memory_entries.assert_awaited_once_with(
        query=query,
        limit=custom_limit,
        agent_id="voxy_brain"
    )

    # Verificar o resultado formatado
    expected_lines = ["Encontrei o seguinte na memória:"]
    expected_lines.extend([f"{i}. Item {i}" for i in range(1, 6)])
    expected_result = "\n".join(expected_lines)
    assert result == expected_result

@patch('app.voxy_agents.tools.memory_tools.get_mem0_manager')
async def test_recall_info_no_results(mock_get_manager):
    """Testa recall_info quando a busca não retorna resultados."""
    # Configurar o mock do manager para retornar lista vazia
    mock_manager = AsyncMock(spec=Mem0Manager)
    mock_manager.is_configured = True
    mock_manager.search_memory_entries = AsyncMock(return_value=[]) # Lista vazia
    mock_get_manager.return_value = mock_manager

    query = "Nada aqui"
    
    # Criar um contexto mock - necessário para invocar a ferramenta
    mock_context = MagicMock()
    
    # Invocando diretamente a função _on_invoke_tool da FunctionTool
    # Convertendo os argumentos para JSON, como o Runner faria
    import json
    args_json = json.dumps({
        "query": query
    })
    
    # Chamar a função embutida na ferramenta
    result = await recall_info.on_invoke_tool(mock_context, args_json)

    # Verificar se search_memory_entries foi chamado
    mock_manager.search_memory_entries.assert_awaited_once_with(
        query=query, limit=3, agent_id="voxy_brain"
    )

    # Verificar a mensagem de "não encontrado"
    assert result == f"Não encontrei nada na memória sobre '{query}'."

@patch('app.voxy_agents.tools.memory_tools.get_mem0_manager')
async def test_recall_info_manager_not_configured(mock_get_manager):
    """Testa recall_info quando o manager não está configurado."""
    # Configurar o mock do manager para não estar configurado
    mock_manager = AsyncMock(spec=Mem0Manager)
    mock_manager.is_configured = False
    mock_get_manager.return_value = mock_manager

    query = "Query irrelevante"
    
    # Criar um contexto mock - necessário para invocar a ferramenta
    mock_context = MagicMock()
    
    # Invocando diretamente a função _on_invoke_tool da FunctionTool
    # Convertendo os argumentos para JSON, como o Runner faria
    import json
    args_json = json.dumps({
        "query": query
    })
    
    # Chamar a função embutida na ferramenta
    result = await recall_info.on_invoke_tool(mock_context, args_json)

    # Verificar que search_memory_entries não foi chamado
    mock_manager.search_memory_entries.assert_not_awaited()

    # Verificar a mensagem de erro
    assert result == "Desculpe, não consigo buscar na memória (configuração)."

@patch('app.voxy_agents.tools.memory_tools.get_mem0_manager')
async def test_recall_info_exception(mock_get_manager):
    """Testa recall_info quando ocorre uma exceção inesperada."""
    # Configurar o mock do manager para levantar exceção
    mock_manager = AsyncMock(spec=Mem0Manager)
    mock_manager.is_configured = True
    mock_manager.search_memory_entries = AsyncMock(side_effect=Exception("Erro de busca simulado"))
    mock_get_manager.return_value = mock_manager

    query = "Query com exceção"
    
    # Criar um contexto mock - necessário para invocar a ferramenta
    mock_context = MagicMock()
    
    # Invocando diretamente a função _on_invoke_tool da FunctionTool
    # Convertendo os argumentos para JSON, como o Runner faria
    import json
    args_json = json.dumps({
        "query": query
    })
    
    # Chamar a função embutida na ferramenta
    result = await recall_info.on_invoke_tool(mock_context, args_json)

    # Verificar que search_memory_entries foi chamado
    mock_manager.search_memory_entries.assert_awaited_once()

    # Verificar a mensagem de erro genérica
    assert result == "Desculpe, erro inesperado ao buscar na memória."

# --- Testes para summarize_memory ---

@patch('app.voxy_agents.tools.memory_tools.get_mem0_manager')
async def test_summarize_memory_success(mock_get_manager):
    """Testa summarize_memory com sucesso, retornando um resumo."""
    # Configurar o mock do manager para retornar memórias
    mock_manager = AsyncMock(spec=Mem0Manager)
    mock_manager.is_configured = True
    mock_memories = [
        {
            "memory": "Lembrete 1",
            "metadata": {"tipo": "lembrete", "categoria": "trabalho"}
        },
        {
            "text": "Preferência de cor: azul", # Testar chave 'text'
            "metadata": {"tipo": "preferencia", "categoria": "visual"}
        },
        {
            "memory": "Fato aleatório",
            "metadata": {"tipo": "outros", "categoria": "geral"}
        },
        {
            "memory": "Memória sem metadados válidos", # Será ignorada
            "metadata": None
        },
         {
            "memory": "Outro lembrete",
            "metadata": {"tipo": "lembrete", "categoria": "pessoal"}
        },
    ]
    mock_manager.get_all_memory_entries = AsyncMock(return_value=mock_memories)
    mock_get_manager.return_value = mock_manager
    
    # Criar um contexto mock - necessário para invocar a ferramenta
    mock_context = MagicMock()
    
    # Invocando diretamente a função _on_invoke_tool da FunctionTool
    # Convertendo os argumentos para JSON, como o Runner faria
    import json
    args_json = json.dumps({})
    
    # Chamar a função embutida na ferramenta
    result = await summarize_memory.on_invoke_tool(mock_context, args_json)

    # Verificar se get_all_memory_entries foi chamado
    mock_manager.get_all_memory_entries.assert_awaited_once_with(agent_id="voxy_brain")

    # Verificar o conteúdo do resultado sem ser muito rígido com a formatação exata
    assert "Resumo do que lembro sobre você:" in result
    assert "Lembretes/Tarefas" in result
    assert "Lembrete 1" in result
    assert "Outro lembrete" in result
    
    # Verificar que a preferência de cor está presente (na categoria "Outros")
    assert "Preferência de cor: azul" in result
    assert "Outros" in result
    assert "Fato aleatório" in result

@patch('app.voxy_agents.tools.memory_tools.get_mem0_manager')
async def test_summarize_memory_no_memories(mock_get_manager):
    """Testa summarize_memory quando não há memórias."""
    # Configurar o mock do manager para retornar lista vazia
    mock_manager = AsyncMock(spec=Mem0Manager)
    mock_manager.is_configured = True
    mock_manager.get_all_memory_entries = AsyncMock(return_value=[]) # Lista vazia
    mock_get_manager.return_value = mock_manager
    
    # Criar um contexto mock - necessário para invocar a ferramenta
    mock_context = MagicMock()
    
    # Invocando diretamente a função _on_invoke_tool da FunctionTool
    # Convertendo os argumentos para JSON, como o Runner faria
    import json
    args_json = json.dumps({})
    
    # Chamar a função embutida na ferramenta
    result = await summarize_memory.on_invoke_tool(mock_context, args_json)

    # Verificar se get_all_memory_entries foi chamado
    mock_manager.get_all_memory_entries.assert_awaited_once_with(agent_id="voxy_brain")

    # Verificar a mensagem de "não encontrado"
    assert result == "Não encontrei memórias registradas."

@patch('app.voxy_agents.tools.memory_tools.get_mem0_manager')
async def test_summarize_memory_no_valid_memories(mock_get_manager):
    """Testa summarize_memory quando há memórias mas nenhuma é válida para processamento."""
    # Configurar o mock do manager para retornar apenas memórias inválidas
    mock_manager = AsyncMock(spec=Mem0Manager)
    mock_manager.is_configured = True
    mock_memories = [
        {"memory": None, "metadata": {}},  # Sem texto
        {"text": None, "metadata": {}},    # Sem texto (alternativo)
        {"memory": "Com texto", "metadata": None},  # Sem metadados
    ]
    mock_manager.get_all_memory_entries = AsyncMock(return_value=mock_memories)
    mock_get_manager.return_value = mock_manager
    
    # Criar um contexto mock - necessário para invocar a ferramenta
    mock_context = MagicMock()
    
    # Invocando diretamente a função _on_invoke_tool da FunctionTool
    # Convertendo os argumentos para JSON, como o Runner faria
    import json
    args_json = json.dumps({})
    
    # Chamar a função embutida na ferramenta
    result = await summarize_memory.on_invoke_tool(mock_context, args_json)

    # Verificar a mensagem específica para o caso
    assert result == "Não encontrei memórias válidas para resumir."

@patch('app.voxy_agents.tools.memory_tools.get_mem0_manager')
async def test_summarize_memory_manager_not_configured(mock_get_manager):
    """Testa summarize_memory quando o manager não está configurado."""
    # Configurar o mock do manager para não estar configurado
    mock_manager = AsyncMock(spec=Mem0Manager)
    mock_manager.is_configured = False
    mock_get_manager.return_value = mock_manager
    
    # Criar um contexto mock - necessário para invocar a ferramenta
    mock_context = MagicMock()
    
    # Invocando diretamente a função _on_invoke_tool da FunctionTool
    # Convertendo os argumentos para JSON, como o Runner faria
    import json
    args_json = json.dumps({})
    
    # Chamar a função embutida na ferramenta
    result = await summarize_memory.on_invoke_tool(mock_context, args_json)

    # Verificar que get_all_memory_entries não foi chamado
    mock_manager.get_all_memory_entries.assert_not_awaited()

    # Verificar a mensagem de erro
    assert result == "Desculpe, não consigo acessar a memória (configuração)."

@patch('app.voxy_agents.tools.memory_tools.get_mem0_manager')
async def test_summarize_memory_exception(mock_get_manager):
    """Testa summarize_memory quando ocorre uma exceção inesperada."""
    # Configurar o mock do manager para levantar exceção
    mock_manager = AsyncMock(spec=Mem0Manager)
    mock_manager.is_configured = True
    mock_manager.get_all_memory_entries = AsyncMock(side_effect=Exception("Erro simulado"))
    mock_get_manager.return_value = mock_manager
    
    # Criar um contexto mock - necessário para invocar a ferramenta
    mock_context = MagicMock()
    
    # Invocando diretamente a função _on_invoke_tool da FunctionTool
    # Convertendo os argumentos para JSON, como o Runner faria
    import json
    args_json = json.dumps({})
    
    # Chamar a função embutida na ferramenta
    result = await summarize_memory.on_invoke_tool(mock_context, args_json)

    # Verificar que get_all_memory_entries foi chamado
    mock_manager.get_all_memory_entries.assert_awaited_once()

    # Verificar a mensagem de erro genérica
    assert result == "Desculpe, erro inesperado ao resumir a memória." 