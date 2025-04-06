# Tarefas do Projeto Voxy

## Pendentes

### **Refatoração: Incluir `username` no Registro (Prioridade: Alta) -> CONCLUÍDO** ✅ 2024-04-06
*Descoberto devido a erro 422 nos testes de registro.*
1.  [x] **(Análise/Ajuste) Modelos (`app/db/models.py`):** Verificar/ajustar modelos Pydantic (`UserCreate`) e SQLModel (`User`, `UserRead`) para incluir `username`. ✅ 2024-04-06
2.  [x] **(Verificação/Ajuste) Endpoint `/register` (`app/api/auth.py`):** Confirmar uso do modelo correto e que `username` é extraído e salvo. Ajustar verificação de duplicidade para `email`. ✅ 2024-04-06
3.  [x] **(Ajuste) Testes de API (`tests/test_api/test_auth.py`):** Incluir `username` nos payloads de teste para `/register` e ajustar asserções. Usar dados únicos. Corrigir status code esperado 404 vs 401 e mensagem. ✅ 2024-04-06
4.  [x] **(Ajuste) Testes Core (`tests/test_core/test_security.py`):** Atualizar helper `register_and_login_user` para incluir `username`. Usar dados únicos. Corrigir asserção de mensagem 401. ✅ 2024-04-06
5.  [x] **(Atualização) Documentação:** Atualizar `PLANNING.md`, `backend/README.md` e `memory-bank`. ✅ 2024-04-06
6.  [x] **(Verificação) Executar Testes:** Rodar `python -m pytest backend` -> 54 PASSED! ✅ 2024-04-06

### **Fase 9: Autenticação e Memória Proativa/Personalizada (Refinamento Restante)**
*As tarefas específicas de Auth/Testes foram concluídas ou incorporadas na refatoração acima.*

1.  **Backend - Refinamento Restante:**
    *   [ ] Considerar uso de Alembic para migrações de banco de dados. (Próximo Passo)
    *   [ ] **Banco de Dados de Teste:** Configurar um banco de dados de teste dedicado (ex: SQLite ou outro DB Postgres) e ajustar fixtures (`conftest.py`) para usá-lo, garantindo isolamento total do ambiente de desenvolvimento.
2.  **Documentação (Finalização Fase 9):**
    *   [ ] Revisar/Atualizar `PLANNING.md` e `backend/README.md` com estado final da Fase 9/Refatoração.
    *   [ ] Atualizar outros `docs/*` se necessário.

### Configuração Inicial (Concluído)
- [x] Criar estrutura de pastas do projeto conforme documentação
- [x] Inicializar repositório Git
- [x] Configurar .gitignore para arquivos sensíveis e temporários
- [x] Criar README.md com instruções básicas do projeto

### Backend (Concluído - Funcionalidades Base)
- [x] Configurar ambiente virtual Python
- [x] Instalar dependências iniciais (FastAPI, OpenAI Agents SDK, etc.) -> **Versões Corrigidas**
    - [x] Corrigir versões em `requirements.txt` (openai-agents, fastapi, pydantic).
    - [x] Fixar `passlib==1.7.4`, `bcrypt==3.2.0` em `requirements.txt`. ✅ 2024-04-05
- [x] Configurar FastAPI básico (`main.py`) (Corrigido prefixo de rota auth) ✅ 2024-04-05
- [x] Criar arquivo `.env.example` para variáveis de ambiente
- [x] Implementar agente básico (brain.py) usando OpenAI Agents SDK
- [x] Criar endpoints de API para chat
- [x] Configurar CORS para permitir comunicação com o frontend
- [x] Implementar testes básicos para o agente e API

### Frontend (Concluído - Funcionalidades Base)
- [x] Inicializar projeto React
- [x] Configurar Tailwind CSS
- [x] Criar componentes básicos de UI
- [x] Implementar interface de chat
- [x] Configurar serviço para comunicação com a API do backend
- [x] Implementar estados para gerenciar a conversa

### Integração (Concluído - Chat Básico)
- [x] Testar comunicação frontend-backend
- [x] Ajustar CORS e outros problemas de integração
- [x] Implementar feedback visual durante processamento das mensagens

### Frontend - Melhoria da UI do Chat (Concluído)
- [x] **Configurar Biblioteca de Componentes (ex: shadcn/ui)**
- [x] **Refatorar Componentes de UI com Novos Estilos**
- [x] **Adicionar Animações e Efeitos (Opcional - Prioridade Média)**
- [x] **Revisar e Refinar Estilos Globais**

### Backend - Ferramentas (Concluído - Weather)
- [x] **Implementar ferramenta `get_weather` (Valor Fixo)**
- [x] **Integrar `get_weather` ao Agente Brain**
- [x] **Implementar ferramenta `get_weather` (API Real - OpenWeatherMap)**

### **Backend - Memória (`mem0.ai` + Supabase) (Concluído Funcionalmente)**
*   [x] Fase 0: Pré-requisitos e Configuração Inicial
*   [x] Fase 1: Implementação da Lógica Base da Memória
*   [x] Fase 2: Testes Unitários para o Gerenciador de Memória
*   [x] Fase 3: Criar Ferramentas para o Agente
*   [x] Fase 4: Integrar Ferramentas ao Agente `brain`
*   [x] Fase 5: Testar a Integração Agente-Ferramentas
*   [x] Fase 6: Testes Manuais e Refinamento
*   [x] Fase 7: Atualização da Documentação

### Documentação (Concluído - Inicial)
- [x] Documentar API com Swagger (Automático FastAPI)
- [x] Criar documentação de exemplo de uso
- [x] Adicionar comentários claros no código

## Em Andamento
*Nenhuma tarefa em andamento no momento.*

## Concluídas
- [x] Definição do escopo inicial do projeto
- [x] Criação dos documentos de planejamento (PLANNING.md e TASK.md)
- [x] Estrutura básica do projeto criada
- [x] Implementação do módulo de agentes (Refatorado para Async)
- [x] Implementação dos endpoints básicos da API (Refatorado para Async)
- [x] Implementação dos componentes de UI do chat (Versão inicial)
- [x] Configuração do ambiente virtual do backend e instalação de dependências (Versões Corrigidas)
- [x] Criação da estrutura de testes e implementação de testes básicos (Adaptados para Async)
- [x] Inicialização do repositório Git
- [x] Correção de erros iniciais do frontend (index.html, index.jsx, manifest.json, index.css)
- [x] Correção de erro 500 (event loop / api key) na comunicação backend
- [x] Refatoração para execução assíncrona do agente concluída com sucesso.
- [x] Teste de comunicação frontend-backend bem-sucedido.
- [x] Correção de versões de dependências em `requirements.txt`.
- [x] Configuração manual do shadcn/ui concluída (Instalação, Tailwind, CSS, Utils, components.json)
- [x] Refatoração do App.jsx concluída
- [x] Refatoração do ChatInput.jsx concluída
- [x] Refatoração do ChatMessage.jsx concluída
- [x] Refatoração do ChatBox.jsx concluída
- [x] **Migração do Frontend de CRA para Vite concluída.**
- [x] **Correção da configuração/instalação do Tailwind CSS v3 no ambiente Vite.**
- [x] **Implementação do tema roxo escuro e avatares no chat.**
- [x] **Implementação inicial da ferramenta `get_weather` (valor fixo).**
- [x] **Criação de testes unitários para a ferramenta `get_weather`.**
- [x] **Integração da ferramenta `get_weather` ao agente `brain`.**
- [x] **Atualização dos testes do agente `brain` para incluir a ferramenta.**
- [x] **Refatoração da ferramenta `get_weather` e correção dos testes.**
- [x] **Implementação da ferramenta `get_weather` com API real (OpenWeatherMap) e tratamento de erros.**
- [x] **Atualização dos testes unitários da ferramenta `get_weather` com mocks para API externa.**
- [x] **Adição de logs de depuração à ferramenta `get_weather`.**
- [x] **Backend - Memória (`mem0.ai` + Supabase) - Fases 0 a 6 concluídas.**
- [x] **Backend - Autenticação - Configuração inicial DB e criação de tabelas verificada.**
- [x] **Backend - Autenticação - Configuração DB, criação tabelas, proteção endpoint chat verificados.**
- [x] **Backend - Adaptação Memória - Concluída (uso de `user_id` via `contextvars`).**
- [x] **Backend - Testes - Configuração estabilizada, testes existentes passando.**
- [x] **Configuração do `shadcn/ui` no Frontend:** ✅ 2024-04-05
- [x] **Correção de Bug: `ChatInput` Duplicado:** ✅ 2024-04-05
- [x] **Correção de Bug: Rota Inicial:** ✅ 2024-04-05
- [x] **Backend: Correção do prefixo da rota de autenticação (`/api/auth`).** ✅ 2024-04-05
- [x] **Backend: Correção da incompatibilidade `passlib`/`bcrypt` (fixando versões).** ✅ 2024-04-05
- [x] **Backend: Correção do `ROLLBACK` na rota `/register` (retorno `UserRead`).** ✅ 2024-04-05
- [x] **Backend: Correção do `ROLLBACK` na rota `/login`
- [x] Refatoração: Incluir `username` no Registro (Análise Modelos, Ajuste Endpoint, Ajuste Testes API/Core, Documentação, Verificação Testes). ✅ 2024-04-06
- [x] Correção de erros de teste (`TypeError` httpx, `AttributeError` TokenData, `PytestWarning` asyncio, `503` DB connection, `422` username missing, `400` email duplicate test logic, `404/401` login logic, `ImportError` email-validator). ✅ 2024-04-06
- [x] Refatoração da fixture de teste de banco de dados (`conftest.py`) para usar sessão dedicada com create/drop tables e rollback. ✅ 2024-04-06

## Descoberto Durante o Trabalho
*   [x] Erro `422 Unprocessable Entity` nos testes de registro devido à falta do campo `username`. (Resolvido) ✅ 2024-04-06
*   [x] Falha no teste de email duplicado devido ao isolamento de transação por chamada de API na fixture de teste inicial. (Resolvido com fixture de sessão dedicada) ✅ 2024-04-06
*   [x] Falha nos testes de login devido a dados não persistentes entre chamadas na mesma função de teste (Resolvido com fixture de sessão dedicada). ✅ 2024-04-06
*   [x] Rota de login incorreta (`/login` vs `/token`). (Resolvido) ✅ 2024-04-06
*   [x] Lógica incorreta para erro 404/401 no login. (Resolvido) ✅ 2024-04-06
*   [x] `ImportError: email-validator is not installed`. (Resolvido) ✅ 2024-04-06