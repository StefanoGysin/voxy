import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock

# Importa a classe e a função que queremos testar
from app.memory.mem0_manager import Mem0Manager, get_mem0_manager, current_user_id_var

# Mock para a classe Memory de mem0ai
# Usamos MagicMock para simular a classe e seus métodos
# MockMemory = MagicMock() # Removido - Criaremos dentro da fixture

# Mock para as configurações (settings)
@pytest.fixture
def mock_settings():
    """ Fixture para mockar as configurações. """
    with patch('app.memory.mem0_manager.settings') as mock_settings:
        # Configuração padrão (sem Supabase)
        # mock_settings.SUPABASE_URL = None # Não mais usado diretamente
        # mock_settings.SUPABASE_SERVICE_ROLE_KEY = None # Não mais usado diretamente
        mock_settings.SUPABASE_CONNECTION_STRING = None # <- Usar este
        mock_settings.OPENAI_API_KEY = "fake_openai_key"
        yield mock_settings

# Fixture para configurar Supabase nas settings mockadas
@pytest.fixture
def mock_settings_with_supabase(mock_settings):
    """ Fixture que modifica mock_settings para incluir Supabase. """
    # mock_settings.SUPABASE_URL = "http://fake-supabase.co" # Não mais usado
    # mock_settings.SUPABASE_SERVICE_ROLE_KEY = "fake_service_key" # Não mais usado
    mock_settings.SUPABASE_CONNECTION_STRING = "postgresql://user:pass@host:port/db" # <- Usar este
    return mock_settings

# Fixture para mockar a classe Memory de mem0ai
@pytest.fixture
def mock_mem0_class():
    """ Fixture para mockar a classe mem0.Memory e seus métodos. """
    # Criar a instância mock dentro da fixture para melhor isolamento
    mock_instance = MagicMock()
    # Mockar explicitamente os métodos usados
    mock_instance.add = MagicMock(return_value="add_success_id")
    mock_instance.search = MagicMock(return_value=[{"id": "1", "memory": "result1"}]) # Usar 'memory' como chave? Verificar documentação/uso real.

    # Mockar o método de classe from_config
    mock_from_config = MagicMock(return_value=mock_instance)

    # Usar um patch aninhado para mockar a classe e seu método de classe
    with patch('app.memory.mem0_manager.Memory', new_callable=MagicMock) as MockMemoryClass:
        MockMemoryClass.return_value = mock_instance # Mock para chamadas a Memory(...)
        MockMemoryClass.from_config = mock_from_config # Mock para chamadas a Memory.from_config(...)
        yield MockMemoryClass # Retorna a classe mockada para asserções (ex: call_count)

# Testes para a inicialização
@pytest.mark.asyncio
async def test_mem0_manager_init_no_supabase(mock_settings, mock_mem0_class):
    """ Testa a inicialização sem as variáveis do Supabase. """
    with patch('app.memory.mem0_manager.mem0_manager_instance', None):
        manager = Mem0Manager()
        assert manager.is_configured is False # Deve ser False se Supabase não configurado
        assert manager.mem0_instance is not None # Deve criar instância padrão
        # Verifica se Memory(...) foi chamado (e não from_config)
        mock_mem0_class.assert_called_once_with(api_key="fake_openai_key")
        mock_mem0_class.from_config.assert_not_called()

@pytest.mark.asyncio
async def test_mem0_manager_init_with_supabase(mock_settings_with_supabase, mock_mem0_class):
    """ Testa a inicialização com as variáveis do Supabase. """
    with patch('app.memory.mem0_manager.mem0_manager_instance', None):
        manager = Mem0Manager()
        assert manager.is_configured is True
        assert manager.mem0_instance is not None
        # Verifica se Memory.from_config foi chamado com a config correta
        mock_mem0_class.from_config.assert_called_once()
        args, kwargs = mock_mem0_class.from_config.call_args
        config_arg = args[0]
        assert config_arg['vector_store']['provider'] == 'supabase'
        assert config_arg['vector_store']['config']['connection_string'] == mock_settings_with_supabase.SUPABASE_CONNECTION_STRING
        assert config_arg['llm']['config']['api_key'] == mock_settings_with_supabase.OPENAI_API_KEY
        # Verifica que Memory() não foi chamado diretamente
        mock_mem0_class.assert_not_called()

@pytest.mark.asyncio
async def test_mem0_manager_init_missing_openai_key(mock_settings, mock_mem0_class):
    """ Testa a inicialização quando a chave OpenAI está faltando. """
    mock_settings.OPENAI_API_KEY = None # Remove a chave
    with patch('app.memory.mem0_manager.mem0_manager_instance', None):
        manager = Mem0Manager()
        assert manager.is_configured is False
        assert manager.mem0_instance is None # Não deve criar a instância
        mock_mem0_class.assert_not_called() # Memory() não deve ser chamado

# Testes para add_memory_entry
@pytest.mark.asyncio
async def test_add_memory_entry_success(mock_settings_with_supabase, mock_mem0_class):
    """ Testa a adição bem-sucedida de uma entrada de memória. """
    with patch('app.memory.mem0_manager.mem0_manager_instance', None):
        manager = Mem0Manager() # Inicializa com Supabase (usa from_config mockado)
        assert manager.is_configured is True
        
        # Pega a instância mockada retornada por from_config
        mock_instance = mock_mem0_class.from_config.return_value
        
        content = "Lembrar desta informação importante."
        metadata = {"source": "test"}
        test_user_id = "user123" # Definir ID para o teste
        agent_id = "agent_test"
        
        # Definir o contextvar para este teste
        token = current_user_id_var.set(test_user_id)
        try:
            success = await manager.add_memory_entry(content, metadata, agent_id)
        finally:
            current_user_id_var.reset(token)
        
        assert success is True
        # Verifica se o método 'add' da instância mockada foi chamado
        # **NÃO** verificamos mais o user_id aqui, pois ele vem do contexto
        mock_instance.add.assert_called_once_with(
            content,
            user_id=test_user_id,
            agent_id=agent_id,
            metadata=metadata
        )

@pytest.mark.asyncio
async def test_add_memory_entry_not_configured(mock_settings, mock_mem0_class):
    """ Testa a falha ao adicionar memória se não configurado (ex: sem API key). """
    mock_settings.OPENAI_API_KEY = None # Simula falha na inicialização
    with patch('app.memory.mem0_manager.mem0_manager_instance', None):
        manager = Mem0Manager()
        assert manager.mem0_instance is None
        
        # Precisa passar user_id aqui também
        # REMOVER: Não passamos mais user_id
        # success = await manager.add_memory_entry(\"conteudo\", user_id=\"user_fail\") 
        # Mesmo se chamássemos, precisaria definir o contextvar, mas o teste é que a instância é None
        success = await manager.add_memory_entry("conteudo") # Chamada sem user_id
        assert success is False
        # Não podemos mais mockar mock_instance diretamente aqui

@pytest.mark.asyncio
async def test_add_memory_entry_exception(mock_settings_with_supabase, mock_mem0_class):
    """ Testa o tratamento de exceção durante a adição. """
    with patch('app.memory.mem0_manager.mem0_manager_instance', None):
        manager = Mem0Manager()
        # Pega a instância mockada retornada por from_config
        mock_instance = mock_mem0_class.from_config.return_value
        # Configura o mock para levantar uma exceção
        mock_instance.add.side_effect = Exception("Falha na adição!")
        
        # Precisa passar user_id
        # REMOVER: Não passamos mais user_id, mas precisamos definir o contextvar
        test_user_id_exc = "user_exception"
        token = current_user_id_var.set(test_user_id_exc)
        try:
            # success = await manager.add_memory_entry(\"conteudo\", user_id=\"user_exception\")
            success = await manager.add_memory_entry("conteudo")
        finally:
            current_user_id_var.reset(token)
            
        assert success is False
        mock_instance.add.assert_called_once() # Verifica se foi chamado

# Testes para search_memory_entries
@pytest.mark.asyncio
async def test_search_memory_entries_success(mock_settings_with_supabase, mock_mem0_class):
    """ Testa a busca bem-sucedida de entradas de memória. """
    with patch('app.memory.mem0_manager.mem0_manager_instance', None):
        manager = Mem0Manager()
        assert manager.is_configured is True
        # Pega a instância mockada retornada por from_config
        mock_instance = mock_mem0_class.from_config.return_value
        
        query = "Informação importante"
        test_user_id_search = "user456" # Definir ID para o teste
        agent_id = "search_agent"
        limit = 3
        
        # Configura o valor de retorno do mock search
        expected_results = [{"id": "mem1", "memory": "info1"}, {"id": "mem2", "memory": "info2"}]
        mock_instance.search.return_value = expected_results
        
        # Definir contextvar para este teste
        token = current_user_id_var.set(test_user_id_search)
        try:
            results = await manager.search_memory_entries(query, agent_id, limit)
        finally:
            current_user_id_var.reset(token)
        
        assert results == expected_results
        # Verifica se o método 'search' foi chamado corretamente
        # **NÃO** verificamos mais o user_id aqui
        mock_instance.search.assert_called_once_with(
            query,
            user_id=test_user_id_search,
            agent_id=agent_id,
            limit=limit
        )

@pytest.mark.asyncio
async def test_search_memory_entries_not_configured(mock_settings, mock_mem0_class):
    """ Testa a falha na busca se não configurado. """
    mock_settings.OPENAI_API_KEY = None
    with patch('app.memory.mem0_manager.mem0_manager_instance', None):
        manager = Mem0Manager()
        assert manager.mem0_instance is None
        
        # Precisa passar user_id
        # REMOVER: Não passamos mais user_id
        # results = await manager.search_memory_entries(\"query\", user_id=\"user_fail\")
        # Mesmo que chamássemos, precisaria definir contextvar, mas teste é que instância é None
        results = await manager.search_memory_entries("query")
        assert results == []
        # Não podemos mais mockar mock_instance diretamente aqui

@pytest.mark.asyncio
async def test_search_memory_entries_exception(mock_settings_with_supabase, mock_mem0_class):
    """ Testa o tratamento de exceção durante a busca. """
    with patch('app.memory.mem0_manager.mem0_manager_instance', None):
        manager = Mem0Manager()
        # Pega a instância mockada retornada por from_config
        mock_instance = mock_mem0_class.from_config.return_value
        mock_instance.search.side_effect = Exception("Falha na busca!")
        
        # Precisa passar user_id
        # REMOVER: Não passamos mais user_id, mas precisamos definir o contextvar
        test_user_id_exc_search = "user_exception"
        token = current_user_id_var.set(test_user_id_exc_search)
        try:
            # results = await manager.search_memory_entries(\"query\", user_id=\"user_exception\")
            results = await manager.search_memory_entries("query")
        finally:
            current_user_id_var.reset(token)
            
        assert results == []
        mock_instance.search.assert_called_once()

@pytest.mark.asyncio
async def test_search_memory_entries_no_results(mock_settings_with_supabase, mock_mem0_class):
    """ Testa o caso em que a busca não retorna resultados. """
    with patch('app.memory.mem0_manager.mem0_manager_instance', None):
        manager = Mem0Manager()
        # Pega a instância mockada retornada por from_config
        mock_instance = mock_mem0_class.from_config.return_value
        mock_instance.search.return_value = [] # Mock retorna lista vazia
        
        # Precisa passar user_id
        # REMOVER: Não passamos mais user_id, mas precisamos definir o contextvar
        test_user_id_empty = "user_empty"
        token = current_user_id_var.set(test_user_id_empty)
        try:
            # results = await manager.search_memory_entries(\"query que não existe\", user_id=\"user_empty\")
            results = await manager.search_memory_entries("query que não existe")
        finally:
            current_user_id_var.reset(token)
            
        assert results == []
        mock_instance.search.assert_called_once()

# Teste para get_mem0_manager (Singleton pattern)
@pytest.mark.asyncio
async def test_get_mem0_manager_singleton(mock_settings_with_supabase, mock_mem0_class):
    """ Testa se get_mem0_manager retorna a mesma instância (Singleton). """
    # Limpa a instância global antes do teste
    with patch('app.memory.mem0_manager.mem0_manager_instance', None):
        # A primeira chamada deve criar a instância e chamar from_config
        manager1 = get_mem0_manager()
        assert mock_mem0_class.from_config.call_count == 1
        # A segunda chamada não deve criar de novo
        manager2 = get_mem0_manager()
        assert manager1 is manager2
        assert mock_mem0_class.from_config.call_count == 1 # Não deve ter chamado de novo

        # Verifica se Memory() não foi chamado diretamente em nenhum momento
        mock_mem0_class.assert_not_called() 