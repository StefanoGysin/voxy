# Backend Voxy (Assíncrono)

Este diretório contém o backend **totalmente assíncrono** da aplicação Voxy, construído com FastAPI e Python >= 3.10.

## Funcionalidades

*   API RESTful **assíncrona** para interação com o agente inteligente (principalmente via `/api/v1/agent/...`).
*   Agente principal (`brain` em `app/voxy_agents/brain.py`) com ferramentas assíncronas para clima (`httpx`) e memória (`mem0ai`).
*   Sistema de autenticação de usuários via **Supabase Auth**. Tokens JWT são emitidos e validados pelo Supabase.
*   **Middleware de Autenticação (`app/middleware.py`):** Valida tokens JWT do Supabase e protege rotas automaticamente.
*   Memória persistente por usuário utilizando `mem0.AsyncMemory` (com backend Supabase).
*   Persistência de sessões e mensagens de chat via tabelas no Supabase (acessadas via `app/services/agent_service.py`).
*   Configuração gerenciada via `pydantic-settings` (`app/core/config.py`).
*   Testes unitários e de integração **assíncronos** com `pytest`, `pytest-asyncio` e `pytest-cov`.

## Configuração

1.  **Ambiente Virtual:** Certifique-se de ter um ambiente virtual Python ativado.
    ```bash
    # Estar dentro do diretório 'backend'
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # ou
    .\venv\Scripts\activate    # Windows
    ```
2.  **Dependências:** Instale as dependências listadas em `requirements.txt`.
    ```bash
    pip install -r requirements.txt
    ```
    **⚠️ Nota sobre `passlib`/`bcrypt`:** Embora a autenticação principal seja via Supabase Auth, `passlib` e `bcrypt` ainda estão listados em `requirements.txt` em versões específicas (`1.7.4` e `3.2.0`). Mantenha estas versões por ora, a menos que uma análise posterior confirme que podem ser removidas com segurança.

3.  **Variáveis de Ambiente:** Copie o arquivo `.env.example` para `.env` (na pasta `backend`) e preencha as variáveis necessárias:
    *   `OPENAI_API_KEY`: Sua chave de API da OpenAI.
    *   `OPENWEATHERMAP_API_KEY`: Sua chave de API do OpenWeatherMap.
    *   `SUPABASE_URL`: URL do seu projeto Supabase.
    *   `SUPABASE_SERVICE_ROLE_KEY`: Chave de serviço (segura) do seu projeto Supabase.
    *   `SUPABASE_CONNECTION_STRING`: Connection string do seu banco de dados Supabase.

4.  **(Opcional - Testes)** Copie `.env.test.example` para `.env.test` (na pasta `backend`) e configure com os detalhes de um projeto Supabase **dedicado para testes**.

## Execução

*   **Servidor de Desenvolvimento (a partir do diretório `backend`):**
    ```bash
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
    A API estará disponível em `http://127.0.0.1:8000`.

*   **Testes (a partir do diretório `backend`):**
    Certifique-se de que o ambiente virtual está ativado e o arquivo `.env.test` está configurado.
    ```bash
    # Executar todos os testes
    python -m pytest
    # ou apenas pytest
    pytest

    # Executar testes com relatório de cobertura
    python -m pytest --cov=app tests/
    # ou pytest --cov=app
    pytest --cov=app
    ```
    *   **Status Atual:** 124 testes passando, 89% de cobertura. ✅

## Estrutura Principal (`backend/app/`)

*   `main.py`: Criação da aplicação FastAPI, inclusão de roteadores e middleware.
*   `middleware.py`: Contém o `AuthMiddleware` para validação de token.
*   `api/`: Contém os roteadores FastAPI (`v1/` e `auth/`).
*   `core/`: Configuração (`config.py`), segurança (`security.py` - pode conter utils legadas), cliente Supabase, exceções.
*   `db/`: Configuração da sessão do banco de dados (`session.py`).
*   `memory/`: Gerenciador da memória `mem0` (`mem0_manager.py`).
*   `schemas/`: Modelos Pydantic para validação de dados da API.
*   `services/`: Lógica de negócios (ex: `agent_service.py`).
*   `voxy_agents/`: Definição do agente (`brain.py`) e suas ferramentas (`tools/`).
