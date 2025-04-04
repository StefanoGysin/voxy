# Arquitetura do Projeto Voxy

Este documento descreve a arquitetura geral, os padrões de design e as decisões técnicas chave do projeto Voxy.

## 1. Visão Geral da Arquitetura

Voxy utiliza uma arquitetura cliente-servidor:

*   **Backend (Servidor):** Uma API RESTful desenvolvida em **Python** com o framework **FastAPI**. É responsável por toda a lógica de negócios, incluindo:
    *   Processamento de linguagem natural.
    *   Gerenciamento e execução de agentes inteligentes usando o **OpenAI Agents SDK**.
    *   Definição e uso de ferramentas (ex: consulta de clima via API externa).
    *   Comunicação com o frontend.
*   **Frontend (Cliente):** Uma Single Page Application (SPA) construída com **React** (usando **Vite** como ferramenta de build). É responsável pela interface do usuário (chat) e pela comunicação com o backend. Utiliza **Tailwind CSS** e a biblioteca de componentes **shadcn/ui** para estilização e UI.

## 2. Padrões de Design e Decisões Técnicas

### Backend

*   **API:** Segue o padrão **RESTful** com FastAPI, aproveitando a validação de dados automática via **Pydantic** e a geração de documentação interativa (Swagger UI).
*   **Agentes:**
    *   Utiliza o **OpenAI Agents SDK** como base.
    *   Possui um **Agente Orquestrador Central (`brain`)** que recebe as mensagens do usuário.
    *   O `brain` utiliza **Ferramentas (`tools`)** para executar tarefas específicas. As ferramentas são funções Python decoradas com `@function_tool`.
    *   **Assincronicidade:** Toda a execução do agente e as ferramentas que envolvem I/O (como chamadas de API) são implementadas usando `async`/`await` para não bloquear o servidor FastAPI.
*   **Modularidade:** O código é organizado em módulos (`api`, `agents`, `core`, etc.) para clareza e manutenibilidade.
*   **Configuração:** Utiliza `pydantic-settings` para carregar configurações (como chaves de API) de variáveis de ambiente e arquivos `.env`.

### Frontend

*   **Componentização:** Segue as melhores práticas do **React**, dividindo a UI em componentes reutilizáveis.
*   **Estilização:** Usa **Tailwind CSS** (utility-first) e componentes pré-construídos de **shadcn/ui**.
*   **Comunicação com API:** Utiliza a `Fetch API` nativa do navegador para chamadas assíncronas ao backend.
*   **Build:** **Vite** é usado para um desenvolvimento rápido e eficiente.

### Comunicação

*   Frontend e backend comunicam-se via **HTTP** usando **JSON** como formato de dados.

## 3. Fluxo de Dados Principal (Exemplo: Consulta de Clima)

```mermaid
graph LR
    A[Usuário envia 'Qual o tempo em Lisboa?' via Chat UI] --> B{Frontend (React)};
    B -- Requisição POST /api/chat --> C{Backend (FastAPI)};
    C -- Chama process_message --> D[Agente Brain (OpenAI SDK)];
    D -- Interpreta e decide usar ferramenta --> E[Ferramenta get_weather (async)];
    E -- Chama API externa --> F[OpenWeatherMap API];
    F -- Retorna dados do tempo --> E;
    E -- Retorna string formatada --> D;
    D -- Retorna resposta final --> C;
    C -- Resposta JSON --> B;
    B -- Atualiza UI --> G[Chat UI exibe resposta];
```

## 4. Considerações Futuras

*   **Múltiplos Agentes:** Uso de `Handoffs` do SDK para delegação entre agentes especializados.
*   **Compartilhamento de Contexto:** Uso de `MCP (Model Context Protocol)` para estados mais complexos entre agentes.
*   **Segurança Aprimorada:** Implementação de `Guardrails` para validação e políticas.
*   **Persistência:** Uso de um banco de dados (SQLAlchemy/SQLModel) para histórico de conversas.
*   **Tratamento de Erros:** Refinar como os erros das ferramentas são comunicados. 