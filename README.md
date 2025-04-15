# Voxy - Agente Inteligente Assíncrono com Memória e Autenticação

Voxy é um sistema baseado em agentes inteligentes construído com o OpenAI Agents SDK. O sistema consiste em um backend **totalmente assíncrono** Python com FastAPI e um frontend React (usando Vite) com Tailwind CSS. Ele suporta **autenticação de usuários via Supabase Auth** e **memória personalizada e persistente** por usuário utilizando `mem0ai` e Supabase.

## Visão Geral

O projeto Voxy utiliza o OpenAI Agents SDK para criar um assistente inteligente capaz de:

*   Conversar com usuários de forma natural.
*   Utilizar ferramentas assíncronas para obter informações externas (ex: clima com OpenWeatherMap via `httpx`).
*   **Autenticar usuários** (registro e login via Supabase Auth).
*   **Memorizar e recordar informações específicas de cada usuário** através de interações, utilizando `mem0.AsyncMemory` com um backend Supabase (PostgreSQL + pgvector).
*   Adaptar suas respostas com base no histórico de memória do usuário logado.

### Arquitetura

- **Backend**: API FastAPI **assíncrona** em Python >= 3.10 que gerencia o agente `brain` (OpenAI SDK), ferramentas assíncronas (`get_weather`, ferramentas de memória), autenticação JWT via **Supabase Auth** (validada por um `AuthMiddleware` centralizado) e a interface com a memória assíncrona `mem0.AsyncMemory`. Utiliza `pydantic-settings` para configuração.
- **Frontend**: Interface de usuário em React (Vite) com Tailwind CSS e shadcn/ui, incluindo fluxo de autenticação (Login/Registro) e a interface de chat principal.

## Funcionalidades Implementadas

*   Chat básico com o agente.
*   Uso da ferramenta `get_weather` (requer chave OpenWeatherMap).
*   Registro de novos usuários via Supabase Auth.
*   Login de usuários existentes via Supabase Auth (recebendo um token JWT do Supabase).
*   Proteção das rotas da API via `AuthMiddleware` - requer token JWT válido do Supabase.
*   Memorização de informações (`memory_tools`) vinculadas ao usuário autenticado.
*   Recuperação de informações (`memory_tools`) da memória do usuário autenticado.
*   Uso proativo da memória pelo agente para contextualizar respostas.
*   **Backend Totalmente Assíncrono:** Todas as operações de I/O são não bloqueantes.
*   **Suíte de Testes Automatizados:** 124 testes passando com 89% de cobertura. ✅

## Primeiros Passos

### Pré-requisitos

*   Python >= 3.10
*   Node.js ~20.x ou superior (compatível com Vite)
*   **Conta Supabase:** Um projeto Supabase com a extensão `vector` habilitada.
*   **Projeto Supabase para Testes (Opcional mas recomendado):** Um segundo projeto Supabase dedicado para rodar os testes automatizados.
*   Chave de API da OpenAI
*   Chave de API do OpenWeatherMap
*   `git` instalado.

### Configuração

1.  **Clonar o Repositório:**
    ```bash
    git clone <url-do-repositorio>
    cd <nome-do-repositorio>
    ```

2.  **Configurar Backend:**
    *   Navegue até a pasta `backend`: `cd backend`
    *   Crie e ative um ambiente virtual Python:
        ```bash
        python -m venv venv
        source venv/bin/activate  # Linux/macOS
        # ou
        .\venv\Scripts\activate  # Windows
        ```
    *   Instale as dependências:
        ```bash
        pip install -r requirements.txt
        ```
    *   **Configure as Variáveis de Ambiente:**
        *   Copie `.env.example` para `.env`: `cp .env.example .env`
        *   Edite o arquivo `.env` com suas chaves de API (OpenAI, OpenWeatherMap) e detalhes do projeto Supabase (URL, Service Role Key, Connection String).
    *   **(Opcional - Testes)** Copie `.env.test.example` para `.env.test` e configure com os detalhes do seu projeto Supabase de **teste**.
    *   Volte para a raiz do projeto: `cd ..`

3.  **Configurar Frontend:**
    *   Navegue até a pasta `frontend`: `cd frontend`
    *   Instale as dependências Node.js:
        ```bash
        npm install
        # ou
        yarn install
        ```
    *   **Configure as Variáveis de Ambiente:**
        *   Copie `.env.example` para `.env`: `cp .env.example .env`
        *   Edite o arquivo `.env` com a URL da sua API backend (`VITE_API_URL`) e os detalhes *públicos* do seu projeto Supabase (`VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`).
    *   Volte para a raiz do projeto: `cd ..`

### Executando a Aplicação

1.  **Iniciar Backend:**
    *   No diretório `backend/`, com o ambiente virtual ativado, execute:
        ```bash
        uvicorn app.main:app --reload
        ```
    *   A API estará rodando em `http://127.0.0.1:8000`.

2.  **Iniciar Frontend:**
    *   No diretório `frontend/`, execute:
        ```bash
        npm run dev
        # ou
        yarn dev
        ```
    *   A aplicação React estará acessível no endereço fornecido (geralmente `http://localhost:5173`).

### Executando os Testes (Backend)

A suíte de testes automatizados do backend utiliza `pytest` e verifica a funcionalidade de diversos componentes (API, serviços, ferramentas, middleware, etc.). Para executá-la:

1.  **Pré-requisito:** Certifique-se de ter configurado o arquivo `backend/.env.test` com as credenciais de um projeto Supabase dedicado para testes. Isso é crucial para evitar que os testes interfiram nos dados do seu ambiente de desenvolvimento ou produção.

2.  **Navegue até o Diretório Backend:** Abra seu terminal e certifique-se de estar na pasta raiz do backend:
    ```bash
    cd backend
    ```

3.  **Ative o Ambiente Virtual:** É essencial que as dependências corretas, incluindo `pytest` e suas extensões (`pytest-asyncio`, `pytest-cov`, etc.), estejam disponíveis. Ative o ambiente virtual que você criou durante a configuração:
    ```bash
    # Windows (PowerShell/CMD):
    .\\venv\\Scripts\\activate
    # Linux/macOS (bash/zsh):
    # source venv/bin/activate
    ```
    Seu prompt de terminal geralmente indicará que o ambiente virtual está ativo (ex: `(venv) C:\\path\\to\\voxy\\backend>`).

4.  **Execute os Testes:** Agora você pode executar a suíte de testes. Use um dos seguintes comandos:

    *   **Execução Padrão:** Este comando descobre e executa todos os testes dentro do diretório `backend/tests/`.
        ```bash
        python -m pytest
        ```
        *Alternativamente, se `pytest` estiver no PATH do seu ambiente virtual, você pode usar apenas:*
        ```bash
        pytest
        ```

    *   **Execução com Relatório de Cobertura:** Para verificar qual porcentagem do código da aplicação (`app/`) é coberta pelos testes, use a flag `--cov=app`. Isso é útil para identificar partes do código que podem precisar de mais testes.
        ```bash
        python -m pytest --cov=app tests/
        ```
        *Ou a forma mais curta:*
        ```bash
        pytest --cov=app
        ```

5.  **Analise a Saída:** O `pytest` exibirá o progresso dos testes (pontos `.` para sucesso, `F` para falha, `E` para erro) e um resumo final indicando o número de testes passados, falhados, etc. Se executar com cobertura, um relatório de cobertura será exibido no final.

*   **Status Atual:** A suíte de testes está robusta, com **124 testes passando** e alcançando **89% de cobertura de código**. ✅

## Detalhes Adicionais

➡️ **Consulte o [README do Backend](./backend/README.md) para informações mais detalhadas sobre a estrutura, API, testes e configuração do backend.**
