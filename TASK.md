# Tarefas do Projeto Voxy

## Pendentes

### **Fase 9: Autenticação e Memória Proativa/Personalizada (Prioridade: Alta -> Em Andamento / Refinamento)**

1.  **Backend - Autenticação (Refinamento):**
    *   [x] **Definir Modelo de Usuário:** Criar modelo `User` em `db/models.py` (SQLModel/SQLAlchemy). ✅ 2024-04-04
    *   [x] **Implementar Hashing de Senha:** Adicionar `passlib[bcrypt]`; usar para hash/verify. (Fixado com `passlib==1.7.4`, `bcrypt==3.2.0`) ✅ 2024-04-05
    *   [x] **Criar Endpoints de Autenticação:** `/register` e `/login` (ou `/token`) em `api/auth.py`. (Corrigido problema de `ROLLBACK`) ✅ 2024-04-05
    *   [x] **Implementar Lógica JWT:** Configurar `python-jose`; criar/decodificar tokens. ✅ 2024-04-04
    *   [x] **Criar Dependência de Autenticação:** `get_current_user` em `core/security.py`. ✅ 2024-04-04
    *   [x] **Garantir funcionamento de `db/session.py` e criação da tabela `user`.** (Corrigido problema de `ROLLBACK` no `get_db`) ✅ 2024-04-05
    *   [ ] **Atualizar Banco de Dados:** Configurar Alembic ou criar tabelas via ORM. (Tabelas criadas via `create_all`, mas Alembic seria melhor para futuras migrações)
    *   [ ] **Escrever testes específicos para autenticação.**
2.  **Backend - Adaptação da Memória:**
    *   [x] **Adaptar `remember_info`/`recall_info` e `Mem0Manager` para usar `user_id`.** ✅ 2024-04-04
    *   [x] **Atualizar `Mem0Manager`:** Usar `user_id` nas chamadas `.add()`/`.search()` (Feito via contextvars). ✅ 2024-04-04
    *   [x] **Revisar/Atualizar Testes de Memória:** Incluir `user_id`. ✅ 2024-04-04
3.  **Backend - Agente e Chat:**
    *   [x] **Proteger endpoint `/api/chat` com `Depends(get_current_user)`.** ✅ 2024-04-04
    *   [x] **Implementar fluxo de passagem do `user_id` para as ferramentas.** ✅ 2024-04-04
    *   [ ] **Aprimorar Instruções do Agente (`brain.py`):** Para memorização proativa/por usuário.
    *   [ ] **Atualizar Testes do Agente (`brain`):** Adaptar testes para autenticação/contexto.
4.  **Frontend - Autenticação e UI (Funcional):**
    *   [x] **Criar Componentes de Autenticação:** Login/Registro (React). ✅ 2024-04-05
    *   [x] **Implementar Fluxo de Autenticação:** Chamadas API, gerenciamento de estado (`AuthContext`), token (`localStorage`), logout. ✅ 2024-04-05
    *   [x] **Proteger Rota do Chat:** Configurar roteamento condicional em `App.jsx`. ✅ 2024-04-05
    *   [x] **Enviar Token com Requisições:** Modificar `sendMessage` para incluir `Authorization: Bearer <token>`. ✅ 2024-04-05
5.  **Documentação (Sub-tarefa da Fase 9):**
    *   [x] Atualizar `memory-bank/*` (activeContext, progress, techContext, systemPatterns). ✅ 2024-04-05
    *   [ ] Atualizar `PLANNING.md` (dependências, `get_db`, `/register` return).
    *   [ ] Atualizar `README.md` (principal e backend) com notas sobre versões `passlib`/`bcrypt`.
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
- [ ] **Testes Manuais:** Testar fluxo completo de autenticação e chat autenticado. (Próximo Passo)
- [ ] **Backend - Refinamento (Fase 9):** Testes de autenticação, Aprimorar Instruções Agente.
- [ ] **Documentação (Fase 9):** Atualizar `PLANNING.md`, `README.md`.

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
- [x] **Backend: Correção do `ROLLBACK` na rota `/login` (commit explícito em `get_db`).** ✅ 2024-04-05
- [x] **Frontend: Implementação das chamadas API de autenticação (`registerUser`, `loginUser`).** ✅ 2024-04-05
- [x] **Frontend: Implementação do `AuthContext` e `AuthProvider`.** ✅ 2024-04-05
- [x] **Frontend: Integração das páginas de Login/Registro com `AuthContext`.** ✅ 2024-04-05
- [x] **Frontend: Proteção de rotas e Logout usando `AuthContext`.** ✅ 2024-04-05
- [x] **Frontend: Envio do token JWT no cabeçalho `Authorization`.** ✅ 2024-04-05

## Descoberto Durante o Trabalho
- [x] Problema inicial com `dlx` vs `npx`. (Resolvido)
- [x] Problema inicial com nome do pacote `shadcn-ui` vs `shadcn`. (Resolvido)
- [x] Necessidade de rodar `init` do `shadcn` antes do `add`. (Resolvido)
- [x] Necessidade de configurar `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json` para alias `@/`. (Resolvido)
- [x] **Incompatibilidade de versão entre `passlib` e `bcrypt` no ambiente.** (Resolvido fixando `passlib==1.7.4`, `bcrypt==3.2.0`) ✅ 2024-04-05
- [x] **`ROLLBACK` inesperado na rota `/register` devido a tipo de retorno vs `response_model`.** (Resolvido retornando `UserRead`) ✅ 2024-04-05
- [x] **`ROLLBACK` inesperado na rota `/login` devido ao gerenciamento de commit/sessão na dependência `get_db`.** (Resolvido com `commit` explícito pós-`yield`) ✅ 2024-04-05
- [x] **Prefixo incorreto na inclusão do `auth_router` em `main.py`.** (Resolvido) ✅ 2024-04-05
