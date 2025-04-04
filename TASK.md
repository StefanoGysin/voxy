# Tarefas do Projeto Voxy

## Pendentes

### Configuração Inicial (Prioridade: Alta)
- [x] Criar estrutura de pastas do projeto conforme documentação
- [x] Inicializar repositório Git
- [x] Configurar .gitignore para arquivos sensíveis e temporários
- [x] Criar README.md com instruções básicas do projeto

### Backend (Prioridade: Alta)
- [x] Configurar ambiente virtual Python
- [x] Instalar dependências iniciais (FastAPI, OpenAI Agents SDK, etc.) -> **Versões Corrigidas**
    - [x] Corrigir versões em `requirements.txt` (openai-agents, fastapi, pydantic).
- [x] Configurar FastAPI básico (`main.py`)
- [x] Criar arquivo `.env.example` para variáveis de ambiente
- [x] Implementar agente básico (brain.py) usando OpenAI Agents SDK
- [x] Criar endpoints de API para chat
- [x] Configurar CORS para permitir comunicação com o frontend
- [x] Implementar testes básicos para o agente e API

### Frontend (Prioridade: Média)
- [x] Inicializar projeto React
- [x] Configurar Tailwind CSS
- [x] Criar componentes básicos de UI
- [x] Implementar interface de chat
- [x] Configurar serviço para comunicação com a API do backend
- [x] Implementar estados para gerenciar a conversa

### Integração (Prioridade: Alta)
- [x] Testar comunicação frontend-backend
- [x] Ajustar CORS e outros problemas de integração
- [x] Implementar feedback visual durante processamento das mensagens

### Frontend - Melhoria da UI do Chat (Prioridade: Alta) -> Concluído nesta fase
- [x] **Configurar Biblioteca de Componentes (ex: shadcn/ui):**
    - [x] Instalar `shadcn/ui` e suas dependências (`tailwindcss`, `lucide-react`, etc.).
    - [x] Configurar `tailwind.config.js` e `globals.css` (ou `index.css`) conforme necessário.
- [x] **Refatorar Componentes de UI com Novos Estilos:**
    - [x] Atualizar `App.jsx` para usar novo layout e componentes.
    - [x] Refatorar `ChatBox.jsx`: Usar `ScrollArea`, aplicar novos estilos.
    - [x] Refatorar `ChatMessage.jsx`: Melhorar aparência das bolhas de mensagem (incluindo ícones).
    - [x] Refatorar `ChatInput.jsx`: Usar `Input` e `Button` estilizados (ex: com ícones).
    - [x] Criar/Usar componentes reutilizáveis (ex: IconButton). (Considerado feito com Button size="icon")
- [ ] **Adicionar Animações e Efeitos (Opcional - Prioridade Média):**
    - [ ] Instalar `framer-motion`.
    - [ ] Adicionar animações sutis a mensagens e elementos da UI.
- [x] **Revisar e Refinar Estilos Globais:**
    - [x] Garantir consistência visual em toda a interface (Implementado tema roxo escuro).

### Backend - Ferramentas (Prioridade: Baixa / Backlog)
- [x] **Implementar ferramenta `get_weather` (Valor Fixo)**:
    - [x] Criar arquivo `backend/app/agents/tools/weather.py`.
    - [x] Definir a função `get_weather(city: str)` usando o decorator `@function_tool`.
    - [x] Adicionar type hints e docstring clara para a ferramenta.
    - [x] (Inicialmente) Retornar um valor fixo (ex: "O tempo em {city} está ensolarado.").
    - [x] Criar testes unitários para `weather.py` em `backend/tests/test_agents/test_tools/`.
- [x] **Integrar `get_weather` ao Agente Brain**:
    - [x] Importar `get_weather` em `backend/app/agents/brain.py`.
    - [x] Modificar `VoxyBrain` para aceitar/adicionar a ferramenta `get_weather`.
    - [x] Atualizar as instruções do `VoxyBrain` para informar ao LLM que ele pode obter informações sobre o tempo.
    - [x] Ajustar/adicionar testes em `test_brain.py` para verificar se a ferramenta foi adicionada.
- [ ] **Implementar ferramenta `get_weather` (API Real):**
    - [ ] Escolher e integrar uma API de clima (ex: OpenWeatherMap).
    - [ ] Atualizar a lógica em `_get_weather_logic`.
    - [ ] Lidar com chaves de API e erros de rede.
    - [ ] Atualizar testes unitários para mockar a chamada de API.
- [x] **Implementar ferramenta `get_weather` (API Real - OpenWeatherMap):**
    - [x] Obter chave de API do OpenWeatherMap.
    - [x] Adicionar chave ao `.env` e `.env.example` do backend (`OPENWEATHERMAP_API_KEY`).
    - [x] Atualizar a lógica em `_get_weather_logic` para chamar a API usando `httpx`.
    - [x] Implementar tratamento de erros (ex: cidade não encontrada, erro na API).
    - [x] Atualizar testes unitários para mockar a chamada à API OpenWeatherMap.
    - [x] Adicionar logs de depuração à ferramenta.

### Documentação (Prioridade: Baixa)
- [ ] Documentar API com Swagger
- [x] Criar documentação de exemplo de uso
- [x] Adicionar comentários claros no código

## Em Andamento (Prioridade: Média)
- [ ] Implementação de ferramentas para o agente (API Real - Próximo passo: **OpenWeatherMap**)
- [ ] Adicionar Animações e Efeitos no Frontend (Opcional - Prioridade Média)

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
