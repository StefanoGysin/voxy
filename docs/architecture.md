# Arquitetura do Projeto Voxy

Este documento descreve a arquitetura geral, os padrões de design e as decisões técnicas chave do projeto Voxy.

## 1. Visão Geral da Arquitetura

Voxy utiliza uma arquitetura cliente-servidor:

*   **Backend (Servidor):** Uma API RESTful desenvolvida em **Python** com o framework **FastAPI**. É responsável por toda a lógica de negócios, incluindo:
    *   Gerenciamento e execução de agentes inteligentes usando o **OpenAI Agents SDK**.
    *   **Autenticação de usuários** (Registro, Login via JWT).
    *   **Gerenciamento de memória de longo prazo por usuário** usando **`mem0ai`** com **Supabase** (Postgres + pgvector) como backend.
    *   Definição e uso de ferramentas (ex: `get_weather`, `remember_info`, `recall_info`).
    *   Comunicação com o frontend.
*   **Frontend (Cliente):** Uma Single Page Application (SPA) construída com **React** (usando **Vite** como ferramenta de build). É responsável pela interface do usuário (chat, login, registro) e pela comunicação com o backend. Utiliza **Tailwind CSS** e a biblioteca de componentes **shadcn/ui** para estilização e UI.

## 2. Padrões de Design e Decisões Técnicas

### Backend

*   **API:** Segue o padrão **RESTful** com FastAPI, aproveitando a validação de dados via **SQLModel/Pydantic** e a geração de documentação interativa (Swagger UI).
*   **Agentes:**
    *   Utiliza o **OpenAI Agents SDK** como base.
    *   Possui um **Agente Orquestrador Central (`brain`)** que recebe as mensagens do usuário.
    *   O `brain` utiliza **Ferramentas (`tools`)** para executar tarefas específicas. As ferramentas são funções Python decoradas com `@function_tool`.
        *   **Estratégia de Memória:** As instruções do agente e as docstrings das ferramentas `remember_info`/`recall_info` foram refinadas para encorajar o uso **proativo** da memória, buscando contexto e memorizando informações relevantes do usuário para personalização.
    *   **Assincronicidade:** Toda a execução do agente e as ferramentas que envolvem I/O (APIs, `mem0ai` via `asyncio.to_thread`) são implementadas usando `async`/`await`.
*   **Memória (`mem0ai`):**
    *   Utiliza a biblioteca `mem0ai` para persistência e busca semântica de informações por usuário.
    *   Interface gerenciada via `Mem0Manager` (Singleton).
    *   Utiliza **Supabase** (Postgres + pgvector) como Vector Store.
    *   O `user_id` para operações de memória é passado via **`contextvars`**, populado após a autenticação do usuário.
*   **Autenticação:**
    *   Baseada em **JWT** (Tokens de Acesso).
    *   Endpoints `/api/auth/register` e `/api/auth/login`.
    *   Hashing de senha com **`passlib[bcrypt]`** (versões fixadas).
    *   Modelo `User` definido com **`SQLModel`**.
    *   Dependência FastAPI `get_current_user` para proteger rotas e obter usuário logado.
    *   Gerenciamento de sessão DB via dependência `get_db` com commit/rollback explícito.
*   **Modularidade:** O código é organizado em módulos (`api`, `agents`, `core`, `db`, `memory`) para clareza e manutenibilidade.
*   **Configuração:** Utiliza `pydantic-settings` para carregar configurações (chaves de API, segredos JWT, conexão DB) de variáveis de ambiente e arquivos `.env`.

### Frontend

*   **Componentização:** Segue as melhores práticas do **React**, dividindo a UI em componentes reutilizáveis.
*   **Estilização:** Usa **Tailwind CSS** (utility-first) e componentes pré-construídos de **shadcn/ui**.
*   **Gerenciamento de Estado (Auth):** Usa **React Context API (`AuthContext`)** para estado de autenticação e persistência do token JWT em **`localStorage`**.
*   **Roteamento:** Utiliza `react-router-dom` para navegação e proteção de rotas.
*   **Comunicação com API:** Utiliza a `Fetch API` nativa do navegador para chamadas assíncronas ao backend, incluindo o envio do token JWT no cabeçalho `Authorization`.
*   **Build:** **Vite** é usado para um desenvolvimento rápido e eficiente.

### Comunicação

*   Frontend e backend comunicam-se via **HTTP** usando **JSON** como formato de dados.
*   Rotas protegidas requerem um token JWT válido (`Bearer <token>`).

## 3. Fluxo de Dados Principal (Exemplo: Chat Autenticado com Memória)

```mermaid
graph TD
    subgraph User Interaction
        A[Usuário Digita Mensagem]
        B[Clica Enviar]
    end
    subgraph Frontend (React + Vite)
        C{Chat UI}
        D[AuthContext]
        E[API Service (fetch)]
    end
    subgraph Backend (FastAPI)
        F[Endpoint /api/chat]
        G[Dep: get_current_user]
        H[process_message(msg, user_id)]
        I[Agent Runner]
        J[Brain Agent]
        K[Tool: recall_info]
        L[Mem0 Manager]
        M[Mem0 SDK]
        N[(DB: Supabase)]
        O[Tool: remember_info (opcional)]
        P[Auth Service (JWT Verify)]
    end

    A --> C
    B -- Aciona Envio --> E
    E -- Lê Token --> D
    E -- Req POST c/ Token & Mensagem --> F
    F -- Chama Dependência --> G
    G -- Valida Token c/ --> P
    G -- Obtém User --> N
    G -- Retorna User --> F
    F -- (Se Válido) Chama --> H
    H -- Define user_id contextvar & Chama --> I
    I -- Executa Agente --> J
    J -- Decide usar memória --> K
    K -- Chama --> L
    L -- Obtém user_id (contextvar) & Chama --> M
    M -- Busca Memória --> N
    N -- Retorna Memórias Relevantes --> M
    M -- Retorna --> L
    L -- Retorna --> K
    K -- Retorna Info --> J
    J -- (Opcional) Decide Salvar Algo --> O
    O -- Chama --> L
    L -- Chama --> M
    M -- Adiciona Memória --> N
    J -- Formula Resposta Final (considerando memória) --> I
    I -- Retorna Resultado --> H
    H -- Retorna Resposta --> F
    F -- Resposta JSON --> E
    E -- Atualiza Estado --> C
    C -- Exibe Resposta ao Usuário --> A
```

## 4. Considerações Futuras

*   **Múltiplos Agentes:** Uso de `Handoffs` do SDK para delegação.
*   **Compartilhamento de Contexto:** Uso de `MCP (Model Context Protocol)`.
*   **Segurança Aprimorada:** `Guardrails`, refresh tokens.
*   **Persistência:** Uso de Alembic para migrações de banco de dados.
*   **Testes:** Adicionar testes para autenticação e adaptar testes do agente. 