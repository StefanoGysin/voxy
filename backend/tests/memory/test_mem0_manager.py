import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import contextvars
from typing import Optional

# Módulo a ser testado
from app.memory.mem0_manager import Mem0Manager, get_mem0_manager, current_user_id_var, mem0_manager_instance
# Importar MemoryConfig aqui para o patch funcionar corretamente no escopo do módulo testado
from mem0.configs.base import MemoryConfig 
from app.core.config import settings

# REMOVER DECORADORES DA CLASSE
# @patch('mem0.memory.main.AsyncMemory', new_callable=MagicMock)
# @patch('app.memory.mem0_manager.MemoryConfig') 
class TestMem0Manager:

    @pytest.fixture
    def mock_async_memory_instance(self):
        """Cria uma instância AsyncMock para ser retornada pelo construtor mockado."""
        return AsyncMock()

    @pytest.fixture(autouse=True)
    def reset_singleton(self, monkeypatch):
        """Fixture para resetar o singleton e o context var antes de cada teste."""
        global mem0_manager_instance
        # Garantir que o singleton seja resetado completamente
        monkeypatch.setattr("app.memory.mem0_manager.mem0_manager_instance", None)
        current_user_id_var.set(None)
        yield # Permite que o teste rode
        # Cleanup após o teste
        monkeypatch.setattr("app.memory.mem0_manager.mem0_manager_instance", None)
        current_user_id_var.set(None)
        # Resetar explicitamente os mocks de classe após cada teste para garantir isolamento
        # Os mocks são injetados nos métodos de teste, então precisamos acessá-los via self
        # No entanto, fixtures não recebem mocks de classe diretamente.
        # O reset automático do patch deve cuidar disso, mas vamos focar na lógica do teste singleton.

    @pytest.fixture
    def mock_settings_configured(self):
        """Mock settings para simular Supabase e OpenAI configurados."""
        with patch('app.memory.mem0_manager.settings') as mock_settings:
            mock_settings.SUPABASE_CONNECTION_STRING = "fake_connection_string"
            mock_settings.OPENAI_API_KEY = "fake_openai_key"
            yield mock_settings

    @pytest.fixture
    def mock_settings_not_configured(self):
        """Mock settings para simular Supabase não configurado."""
        with patch('app.memory.mem0_manager.settings') as mock_settings:
            mock_settings.SUPABASE_CONNECTION_STRING = None
            mock_settings.OPENAI_API_KEY = "fake_openai_key" # OpenAI ainda pode estar configurado
            yield mock_settings

    # --- Testes de Inicialização (__init__) ---

    # ADICIONAR DECORADORES AO MÉTODO
    @pytest.mark.asyncio
    @patch('app.memory.mem0_manager.MemoryConfig') 
    @patch('mem0.memory.main.AsyncMemory', new_callable=MagicMock)
    async def test_init_success(self, mock_AsyncMemory: MagicMock, mock_MemoryConfig: MagicMock, mock_settings_configured, mock_async_memory_instance: AsyncMock):
        """Testa a inicialização bem-sucedida do Mem0Manager."""
        # Configurar Mocks ANTES de instanciar
        mock_config_instance = MagicMock()
        mock_MemoryConfig.return_value = mock_config_instance
        mock_AsyncMemory.return_value = mock_async_memory_instance # Configurar o retorno do construtor

        manager = Mem0Manager()
        assert manager.is_configured is True
        # A instância deve ser o AsyncMock que configuramos para ser retornado
        assert manager.mem0_instance is mock_async_memory_instance

        # Verificar se MemoryConfig foi chamado
        expected_config_dict = {
            "vector_store": {
                "provider": "supabase",
                "config": {
                    "connection_string": "fake_connection_string",
                    "collection_name": "memories",
                }
            },
            "llm": {
                "provider": "openai",
                "config": {"api_key": "fake_openai_key"}
            }
        }
        mock_MemoryConfig.assert_called_once_with(**expected_config_dict)

        # Verificar se o CONSTRUTOR de AsyncMemory foi chamado com a instância mockada de MemoryConfig
        mock_AsyncMemory.assert_called_once_with(config=mock_config_instance)

    # ADICIONAR DECORADORES AO MÉTODO (mesmo que não sejam usados ativamente, para consistência ou futuras verificações)
    @pytest.mark.asyncio
    @patch('app.memory.mem0_manager.MemoryConfig') 
    @patch('mem0.memory.main.AsyncMemory', new_callable=MagicMock)
    async def test_init_no_supabase_connection(self, mock_AsyncMemory: MagicMock, mock_MemoryConfig: MagicMock, mock_settings_not_configured, mock_async_memory_instance: AsyncMock):
        """Testa a inicialização quando SUPABASE_CONNECTION_STRING não está definido."""
        # Nenhuma configuração de mock necessária aqui, pois esperamos que não sejam chamados
        manager = Mem0Manager()
        assert manager.is_configured is False
        assert manager.mem0_instance is None
        mock_AsyncMemory.assert_not_called() # AsyncMemory não deve ser instanciado
        mock_MemoryConfig.assert_not_called() # MemoryConfig também não deve ser instanciado

    # ADICIONAR DECORADORES AO MÉTODO
    @pytest.mark.asyncio
    @patch('app.memory.mem0_manager.MemoryConfig') 
    @patch('mem0.memory.main.AsyncMemory', new_callable=MagicMock)
    async def test_init_no_openai_key(self, mock_AsyncMemory: MagicMock, mock_MemoryConfig: MagicMock, mock_settings_configured, mock_async_memory_instance: AsyncMock):
        """Testa a inicialização quando OPENAI_API_KEY não está definido."""
        # Nenhuma configuração de mock necessária aqui
        with patch('app.memory.mem0_manager.settings') as mock_settings:
            mock_settings.SUPABASE_CONNECTION_STRING = "fake_connection_string"
            mock_settings.OPENAI_API_KEY = None
            manager = Mem0Manager()
            assert manager.is_configured is False
            assert manager.mem0_instance is None
            mock_AsyncMemory.assert_not_called() # AsyncMemory não deve ser instanciado devido ao ValueError
            # MemoryConfig PODE ser chamado antes do ValueError ser levantado, dependendo da ordem interna.
            # Para simplificar, não vamos assertar a chamada de mock_MemoryConfig aqui.
            # A asserção principal é que is_configured é False e AsyncMemory não foi chamado.

    # ADICIONAR DECORADORES AO MÉTODO
    @pytest.mark.asyncio
    @patch('app.memory.mem0_manager.MemoryConfig') 
    @patch('mem0.memory.main.AsyncMemory', new_callable=MagicMock)
    async def test_init_import_error(self, mock_AsyncMemory: MagicMock, mock_MemoryConfig: MagicMock, mock_settings_configured, mock_async_memory_instance: AsyncMock):
        """Testa a inicialização quando ocorre um ImportError ao instanciar AsyncMemory."""
        # Configurar Mocks ANTES de instanciar
        mock_config_instance = MagicMock()
        mock_MemoryConfig.return_value = mock_config_instance
        mock_AsyncMemory.side_effect = ImportError("Psycopg2 não encontrado") # Configurar side_effect
        # mock_AsyncMemory.return_value não é relevante aqui pois side_effect tem prioridade

        manager = Mem0Manager()
        assert manager.is_configured is False
        assert manager.mem0_instance is None
        # MemoryConfig foi chamado
        mock_MemoryConfig.assert_called_once()
        # O construtor de AsyncMemory foi chamado (e levantou o erro)
        mock_AsyncMemory.assert_called_once_with(config=mock_config_instance)

    # --- Testes do Singleton (get_mem0_manager) ---
    
    # ADICIONAR DECORADORES AO MÉTODO
    # Nota: get_mem0_manager não é async, então removemos @pytest.mark.asyncio daqui
    @patch('app.memory.mem0_manager.MemoryConfig') 
    @patch('mem0.memory.main.AsyncMemory', new_callable=MagicMock)
    def test_get_mem0_manager_singleton(self, mock_AsyncMemory: MagicMock, mock_MemoryConfig: MagicMock, mock_settings_configured, mock_async_memory_instance: AsyncMock):
        """Testa se get_mem0_manager retorna a mesma instância (singleton)."""
        # Configurar Mocks ANTES da primeira chamada a get_mem0_manager
        mock_config_instance = MagicMock()
        mock_MemoryConfig.return_value = mock_config_instance
        mock_AsyncMemory.return_value = mock_async_memory_instance

        manager1 = get_mem0_manager()
        # Verificar chamadas na primeira vez
        mock_MemoryConfig.assert_called_once()
        mock_AsyncMemory.assert_called_once()
        # Guardar a contagem de chamadas
        memory_config_call_count = mock_MemoryConfig.call_count
        async_memory_call_count = mock_AsyncMemory.call_count

        # Resetar mocks para verificar se são chamados novamente (não devem ser) - REMOVIDO, causa erro.
        # mock_MemoryConfig.reset_mock()
        # mock_AsyncMemory.reset_mock()
        manager2 = get_mem0_manager()
        
        assert manager1 is manager2
        assert manager1.is_configured is True
        # Mocks de construtor devem ter sido chamados apenas uma vez na primeira chamada
        # Verificar que a contagem de chamadas não aumentou
        assert mock_MemoryConfig.call_count == memory_config_call_count
        assert mock_AsyncMemory.call_count == async_memory_call_count

    # ESTE TESTE NÃO PRECISA DOS DECORADORES @patch
    @pytest.mark.asyncio
    async def test_get_mem0_manager_not_configured(self, monkeypatch):
        """
        Testa se get_mem0_manager retorna uma instância não configurada 
        quando SUPABASE_CONNECTION_STRING está ausente.
        """
        # Garantir que a instância global seja resetada para este teste
        monkeypatch.setattr("app.memory.mem0_manager.mem0_manager_instance", None)
        
        # Simular que a configuração não está definida
        monkeypatch.setattr(settings, "SUPABASE_CONNECTION_STRING", None)

        # Chamar o getter
        manager = get_mem0_manager()

        # Verificar se a instância foi retornada, mas não está configurada
        assert manager is not None
        assert not manager.is_configured # << CORRIGIDO
        # assert True is False # << REMOVIDO

    # --- Testes de add_memory_entry ---

    # ADICIONAR DECORADORES AO MÉTODO
    @pytest.mark.asyncio
    @patch('app.memory.mem0_manager.MemoryConfig') 
    @patch('mem0.memory.main.AsyncMemory')
    async def test_add_memory_entry_success(self, mock_AsyncMemory, mock_MemoryConfig, mock_settings_configured):
        """Testa adicionar uma entrada de memória com sucesso."""
        # Resetar explicitamente o singleton para garantir um novo manager
        global mem0_manager_instance
        mem0_manager_instance = None
        
        test_user_id = "user_123"
        current_user_id_var.set(test_user_id) # Define o user_id no contexto

        # Criar uma instância mock com add como AsyncMock
        mock_instance = MagicMock()
        mock_instance.add = AsyncMock()
        mock_instance.add.return_value = {"some_result": "success"}
        
        # Configurar o mock do construtor para retornar nossa instância mock
        mock_AsyncMemory.return_value = mock_instance
        mock_MemoryConfig.return_value = MagicMock()

        # Obter o manager (inicializa com nosso mock)
        manager = get_mem0_manager()
        assert manager.is_configured is True
        assert manager.mem0_instance is mock_instance

        # Executar o método de teste
        content = "Lembrar desta informação importante"
        metadata = {"tipo": "fato", "categoria": "teste"}
        agent_id = "test_agent"

        success = await manager.add_memory_entry(content=content, metadata=metadata, agent_id=agent_id)

        # Verificar resultado
        assert success is True
        
        # Verificar se o método add da instância mockada foi chamado
        mock_instance.add.assert_awaited_once()

        # Verificar os argumentos passados para add
        call_args, call_kwargs = mock_instance.add.call_args
        expected_messages = [{"role": "user", "content": content}]
        assert call_kwargs.get('messages') == expected_messages
        assert call_kwargs.get('user_id') == test_user_id
        assert call_kwargs.get('agent_id') == agent_id
        assert call_kwargs.get('metadata') == metadata

    # ADICIONAR DECORADORES AO MÉTODO
    @pytest.mark.asyncio
    @patch('app.memory.mem0_manager.MemoryConfig') 
    @patch('mem0.memory.main.AsyncMemory', new_callable=MagicMock)
    async def test_add_memory_entry_not_configured(self, mock_AsyncMemory: MagicMock, mock_MemoryConfig: MagicMock, mock_settings_not_configured, mock_async_memory_instance: AsyncMock):
        """Testa adicionar memória quando o manager não está configurado."""
        # Garantir que o singleton seja resetado
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr("app.memory.mem0_manager.mem0_manager_instance", None)
        
        # Garantir que o mock_settings_not_configured seja realmente usado
        # Isso é necessário porque o patch de 'app.memory.mem0_manager.settings' pode não estar
        # sendo aplicado corretamente em todos os testes
        with patch('app.memory.mem0_manager.settings.SUPABASE_CONNECTION_STRING', None):
            manager = get_mem0_manager() # Pega a instância não configurada
            assert manager.is_configured is False

            success = await manager.add_memory_entry(content="teste", metadata={})
            assert success is False
            
        # add não deve ser chamado na instância mockada
        mock_async_memory_instance.add.assert_not_awaited()
        monkeypatch.undo()

    # ADICIONAR DECORADORES AO MÉTODO
    @pytest.mark.asyncio
    @patch('app.memory.mem0_manager.MemoryConfig') 
    @patch('mem0.memory.main.AsyncMemory', new_callable=MagicMock)
    async def test_add_memory_entry_no_user_id(self, mock_AsyncMemory: MagicMock, mock_MemoryConfig: MagicMock, mock_settings_configured, mock_async_memory_instance: AsyncMock):
        """Testa adicionar memória quando user_id não está no contexto."""
        current_user_id_var.set(None) # Garante que user_id é None

        # Configurar Mocks ANTES de chamar get_mem0_manager
        mock_config_instance = MagicMock()
        mock_MemoryConfig.return_value = mock_config_instance
        mock_AsyncMemory.return_value = mock_async_memory_instance

        manager = get_mem0_manager()
        # A instância mockada é mock_async_memory_instance

        success = await manager.add_memory_entry(content="teste", metadata={})
        assert success is False
        # add não deve ser chamado na instância mockada
        mock_async_memory_instance.add.assert_not_awaited()

    # ADICIONAR DECORADORES AO MÉTODO
    @pytest.mark.asyncio
    @patch('app.memory.mem0_manager.MemoryConfig') 
    @patch('mem0.memory.main.AsyncMemory', new_callable=MagicMock)
    async def test_add_memory_entry_exception(self, mock_AsyncMemory: MagicMock, mock_MemoryConfig: MagicMock, mock_settings_configured, mock_async_memory_instance: AsyncMock):
        """Testa adicionar memória quando mem0.add levanta uma exceção."""
        # Garantir que o singleton seja resetado
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr("app.memory.mem0_manager.mem0_manager_instance", None)
        
        test_user_id = "user_456"
        current_user_id_var.set(test_user_id)

        # Configurar Mocks ANTES de chamar get_mem0_manager
        mock_config_instance = MagicMock()
        mock_MemoryConfig.return_value = mock_config_instance
        
        # Criar uma instância mock com add que lança exceção
        mock_instance = MagicMock()
        mock_instance.add = AsyncMock(side_effect=Exception("Erro na API do Mem0"))
        mock_AsyncMemory.return_value = mock_instance
        
        manager = get_mem0_manager()
        assert manager.is_configured is True
        
        # Tentar adicionar memória, que deve causar exceção internamente
        success = await manager.add_memory_entry(content="teste", metadata={})
        assert success is False
        
        # add foi chamado e falhou
        mock_instance.add.assert_awaited_once()
        monkeypatch.undo()

    # --- Testes de search_memory_entries ---

    # ADICIONAR DECORADORES AO MÉTODO
    @pytest.mark.asyncio
    @patch('app.memory.mem0_manager.MemoryConfig') 
    @patch('mem0.memory.main.AsyncMemory', new_callable=MagicMock)
    async def test_search_memory_entries_success(self, mock_AsyncMemory: MagicMock, mock_MemoryConfig: MagicMock, mock_settings_configured):
        """Testa buscar entradas de memória com sucesso."""
        # Garantir que o singleton seja resetado
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr("app.memory.mem0_manager.mem0_manager_instance", None)
        
        test_user_id = "user_search_1"
        current_user_id_var.set(test_user_id)

        # Criar instância mock com search configurado corretamente
        mock_instance = MagicMock()
        mock_return = [{"id": "mem1", "memory": "resultado 1"}, {"id": "mem2", "memory": "resultado 2"}]
        mock_instance.search = AsyncMock(return_value={"results": mock_return})
        
        # Configurar mocks
        mock_config_instance = MagicMock()
        mock_MemoryConfig.return_value = mock_config_instance
        mock_AsyncMemory.return_value = mock_instance

        manager = get_mem0_manager()
        assert manager.is_configured is True
        assert manager.mem0_instance is mock_instance

        query = "Qual o resultado?"
        agent_id = "search_agent"
        limit = 5

        results = await manager.search_memory_entries(query=query, agent_id=agent_id, limit=limit)

        assert results == mock_return
        # Verifica chamada no método search da instância mockada
        mock_instance.search.assert_awaited_once_with(
            query=query,
            user_id=test_user_id,
            agent_id=agent_id,
            limit=limit
        )
        monkeypatch.undo()

    # ADICIONAR DECORADORES AO MÉTODO
    @pytest.mark.asyncio
    @patch('app.memory.mem0_manager.MemoryConfig') 
    @patch('mem0.memory.main.AsyncMemory', new_callable=MagicMock)
    async def test_search_memory_entries_no_results(self, mock_AsyncMemory: MagicMock, mock_MemoryConfig: MagicMock, mock_settings_configured):
        """Testa buscar memória quando não há resultados."""
        # Garantir que o singleton seja resetado
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr("app.memory.mem0_manager.mem0_manager_instance", None)
        
        test_user_id = "user_search_2"
        current_user_id_var.set(test_user_id)

        # Criar instância mock com search retornando lista vazia
        mock_instance = MagicMock()
        mock_instance.search = AsyncMock(return_value={"results": []})
        
        # Configurar mocks
        mock_config_instance = MagicMock()
        mock_MemoryConfig.return_value = mock_config_instance
        mock_AsyncMemory.return_value = mock_instance

        manager = get_mem0_manager()
        assert manager.is_configured is True
        assert manager.mem0_instance is mock_instance

        results = await manager.search_memory_entries(query="query inexistente")
        assert results == []
        # Verifica chamada no método search da instância mockada
        mock_instance.search.assert_awaited_once()
        monkeypatch.undo()

    # ADICIONAR DECORADORES AO MÉTODO
    @pytest.mark.asyncio
    @patch('app.memory.mem0_manager.MemoryConfig') 
    @patch('mem0.memory.main.AsyncMemory', new_callable=MagicMock)
    async def test_search_memory_entries_not_configured(self, mock_AsyncMemory: MagicMock, mock_MemoryConfig: MagicMock, mock_settings_not_configured, mock_async_memory_instance: AsyncMock):
        """Testa buscar memória quando o manager não está configurado."""
        # Nenhuma configuração de mock necessária
        manager = get_mem0_manager()
        results = await manager.search_memory_entries(query="teste")
        assert results == []
        mock_AsyncMemory.assert_not_called() # Não deve chamar AsyncMemory
        mock_MemoryConfig.assert_not_called()
        if manager.mem0_instance: # Defensivo, mas deve ser None
            # A instância aqui seria mock_async_memory_instance se configurada
            mock_async_memory_instance.search.assert_not_awaited()

    # ADICIONAR DECORADORES AO MÉTODO
    @pytest.mark.asyncio
    @patch('app.memory.mem0_manager.MemoryConfig') 
    @patch('mem0.memory.main.AsyncMemory', new_callable=MagicMock)
    async def test_search_memory_entries_no_user_id(self, mock_AsyncMemory: MagicMock, mock_MemoryConfig: MagicMock, mock_settings_configured, mock_async_memory_instance: AsyncMock):
        """Testa buscar memória quando user_id não está no contexto."""
        current_user_id_var.set(None)

        # Configurar Mocks ANTES de chamar get_mem0_manager
        mock_config_instance = MagicMock()
        mock_MemoryConfig.return_value = mock_config_instance
        mock_AsyncMemory.return_value = mock_async_memory_instance

        manager = get_mem0_manager()
        results = await manager.search_memory_entries(query="teste")
        assert results == []
        # Verifica que search não foi chamado na instância mockada
        mock_async_memory_instance.search.assert_not_awaited()

    # ADICIONAR DECORADORES AO MÉTODO
    @pytest.mark.asyncio
    @patch('app.memory.mem0_manager.MemoryConfig') 
    @patch('mem0.memory.main.AsyncMemory', new_callable=MagicMock)
    async def test_search_memory_entries_exception(self, mock_AsyncMemory: MagicMock, mock_MemoryConfig: MagicMock, mock_settings_configured):
        """Testa buscar memória quando mem0.search levanta uma exceção."""
        # Garantir que o singleton seja resetado
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr("app.memory.mem0_manager.mem0_manager_instance", None)
        
        test_user_id = "user_search_err"
        current_user_id_var.set(test_user_id)

        # Criar instância mock com search lançando exceção
        mock_instance = MagicMock()
        mock_instance.search = AsyncMock(side_effect=Exception("Erro na busca Mem0"))
        
        # Configurar mocks
        mock_config_instance = MagicMock()
        mock_MemoryConfig.return_value = mock_config_instance
        mock_AsyncMemory.return_value = mock_instance

        manager = get_mem0_manager()
        assert manager.is_configured is True
        assert manager.mem0_instance is mock_instance

        results = await manager.search_memory_entries(query="teste")
        assert results == []
        # Verifica que search foi chamado na instância mockada (e falhou)
        mock_instance.search.assert_awaited_once()
        monkeypatch.undo()

    # --- Testes de get_all_memory_entries ---

    # ADICIONAR DECORADORES AO MÉTODO
    @pytest.mark.asyncio
    @patch('app.memory.mem0_manager.MemoryConfig') 
    @patch('mem0.memory.main.AsyncMemory', new_callable=MagicMock)
    async def test_get_all_memory_entries_success(self, mock_AsyncMemory: MagicMock, mock_MemoryConfig: MagicMock, mock_settings_configured):
        """Testa buscar todas as entradas de memória com sucesso."""
        # Garantir que o singleton seja resetado
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr("app.memory.mem0_manager.mem0_manager_instance", None)
        
        test_user_id = "user_getall_1"
        current_user_id_var.set(test_user_id)

        # Criar instância mock com get_all configurado corretamente
        mock_instance = MagicMock()
        mock_return = [{"id": "mem_a", "memory": "tudo 1"}, {"id": "mem_b", "memory": "tudo 2"}]
        mock_instance.get_all = AsyncMock(return_value=mock_return)
        
        # Configurar mocks
        mock_config_instance = MagicMock()
        mock_MemoryConfig.return_value = mock_config_instance
        mock_AsyncMemory.return_value = mock_instance

        manager = get_mem0_manager()
        assert manager.is_configured is True
        assert manager.mem0_instance is mock_instance

        agent_id = "getall_agent" # Embora o código não use mais, vamos passar

        results = await manager.get_all_memory_entries(agent_id=agent_id)

        assert results == mock_return
        # Verifica chamada no método get_all da instância mockada
        mock_instance.get_all.assert_awaited_once_with(
            user_id=test_user_id
            # agent_id não é mais passado para mem0.get_all
        )
        monkeypatch.undo()

    # ADICIONAR DECORADORES AO MÉTODO
    @pytest.mark.asyncio
    @patch('app.memory.mem0_manager.MemoryConfig') 
    @patch('mem0.memory.main.AsyncMemory', new_callable=MagicMock)
    async def test_get_all_memory_entries_no_results(self, mock_AsyncMemory: MagicMock, mock_MemoryConfig: MagicMock, mock_settings_configured):
        """Testa buscar todas as memórias quando não há resultados."""
        # Garantir que o singleton seja resetado
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr("app.memory.mem0_manager.mem0_manager_instance", None)
        
        test_user_id = "user_getall_2"
        current_user_id_var.set(test_user_id)

        # Criar instância mock com get_all retornando lista vazia
        mock_instance = MagicMock()
        mock_instance.get_all = AsyncMock(return_value=[])
        
        # Configurar mocks
        mock_config_instance = MagicMock()
        mock_MemoryConfig.return_value = mock_config_instance
        mock_AsyncMemory.return_value = mock_instance

        manager = get_mem0_manager()
        assert manager.is_configured is True
        assert manager.mem0_instance is mock_instance

        results = await manager.get_all_memory_entries()
        assert results == []
        # Verifica chamada no método get_all da instância mockada
        mock_instance.get_all.assert_awaited_once()
        monkeypatch.undo()

    # ADICIONAR DECORADORES AO MÉTODO
    @pytest.mark.asyncio
    @patch('app.memory.mem0_manager.MemoryConfig') 
    @patch('mem0.memory.main.AsyncMemory', new_callable=MagicMock)
    async def test_get_all_memory_entries_exception(self, mock_AsyncMemory: MagicMock, mock_MemoryConfig: MagicMock, mock_settings_configured):
        """Testa buscar todas as memórias quando mem0.get_all levanta uma exceção."""
        # Garantir que o singleton seja resetado
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr("app.memory.mem0_manager.mem0_manager_instance", None)
        
        test_user_id = "user_getall_err"
        current_user_id_var.set(test_user_id)

        # Criar instância mock com get_all lançando exceção
        mock_instance = MagicMock()
        mock_instance.get_all = AsyncMock(side_effect=Exception("Erro no get_all Mem0"))
        
        # Configurar mocks
        mock_config_instance = MagicMock()
        mock_MemoryConfig.return_value = mock_config_instance
        mock_AsyncMemory.return_value = mock_instance

        manager = get_mem0_manager()
        assert manager.is_configured is True
        assert manager.mem0_instance is mock_instance

        results = await manager.get_all_memory_entries()
        assert results == []
        # Verifica que get_all foi chamado na instância mockada (e falhou)
        mock_instance.get_all.assert_awaited_once()
        monkeypatch.undo()

    @pytest.mark.asyncio
    @patch('app.memory.mem0_manager.MemoryConfig') 
    @patch('mem0.memory.main.AsyncMemory', new_callable=MagicMock)
    async def test_get_all_memory_entries_not_configured(self, mock_AsyncMemory: MagicMock, mock_MemoryConfig: MagicMock, mock_settings_not_configured):
        """Testa buscar todas as memórias quando o manager não está configurado."""
        # Garantir que o singleton seja resetado
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr("app.memory.mem0_manager.mem0_manager_instance", None)
        
        # Garantir que o mock_settings_not_configured seja realmente usado
        with patch('app.memory.mem0_manager.settings.SUPABASE_CONNECTION_STRING', None):
            manager = get_mem0_manager()
            assert manager.is_configured is False
            
            results = await manager.get_all_memory_entries()
            assert results == []
            
        # Verificações adicionais
        mock_AsyncMemory.assert_not_called()
        mock_MemoryConfig.assert_not_called()
        monkeypatch.undo()

    @pytest.mark.asyncio
    @patch('app.memory.mem0_manager.MemoryConfig') 
    @patch('mem0.memory.main.AsyncMemory', new_callable=MagicMock)
    async def test_get_all_memory_entries_no_user_id(self, mock_AsyncMemory: MagicMock, mock_MemoryConfig: MagicMock, mock_settings_configured):
        """Testa buscar todas as memórias quando user_id não está no contexto."""
        # Garantir que o singleton seja resetado
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr("app.memory.mem0_manager.mem0_manager_instance", None)
        
        # Garantir que user_id seja None
        current_user_id_var.set(None)

        # Criar instância mock
        mock_instance = MagicMock()
        mock_instance.get_all = AsyncMock()
        
        # Configurar mocks
        mock_config_instance = MagicMock()
        mock_MemoryConfig.return_value = mock_config_instance
        mock_AsyncMemory.return_value = mock_instance

        manager = get_mem0_manager()
        assert manager.is_configured is True
        assert manager.mem0_instance is mock_instance

        results = await manager.get_all_memory_entries()
        assert results == []
        # Verifica que get_all não foi chamado na instância mockada
        mock_instance.get_all.assert_not_awaited()
        monkeypatch.undo()

# Garante uma nova linha no final do arquivo para corrigir possíveis erros de lint