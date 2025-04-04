# Voxy - Agente Inteligente

Voxy é um sistema baseado em agentes inteligentes construído com o OpenAI Agents SDK. O sistema consiste em um backend Python com FastAPI e um frontend React (usando **Vite**) com Tailwind CSS.

## Visão Geral

O projeto Voxy utiliza o OpenAI Agents SDK para criar um assistente inteligente que pode ser estendido para trabalhar com múltiplos agentes especializados. A arquitetura é composta por:

- **Backend**: API FastAPI em Python com agentes baseados no OpenAI Agents SDK
- **Frontend**: Interface de usuário em React (construída com **Vite**) com Tailwind CSS para comunicação com o agente

## Primeiros Passos

### Pré-requisitos

- Python 3.12.8
- Node.js ~20.x (v20.14.0 ou compatível)
- Chave de API da OpenAI
- Chave de API do OpenWeatherMap (para funcionalidade de clima)

### Configuração do Backend

1. Navegue até a pasta do backend:
   ```bash
   cd backend
   ```

2. Crie um ambiente virtual:
   ```bash
   python -m venv venv
   ```

3. Ative o ambiente virtual:
   - Windows:
     ```
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

5. Crie um arquivo `.env` a partir do `.env.example`:
   ```bash
   cp .env.example .env
   ```
   Então, edite o arquivo `.env` e adicione suas chaves de API:
     - `OPENAI_API_KEY`: Obtida no site da OpenAI.
     - `OPENWEATHERMAP_API_KEY`: Obtida no site do OpenWeatherMap (necessária para a ferramenta de clima).

6. Execute o servidor de desenvolvimento:
   ```bash
   uvicorn app.main:app --reload
   ```

O servidor estará disponível em http://localhost:8000.

### Configuração do Frontend

1. Navegue até a pasta do frontend:
   ```bash
   cd frontend
   ```

2. Instale as dependências:
   ```bash
   npm install
   ```

3. Crie um arquivo `.env` na raiz da pasta `frontend/` (opcional para execução local padrão):
   ```
   # Exemplo: Define a URL da API do backend se não for http://localhost:8000/api
   VITE_API_URL=http://seu_backend_url/api
   ```
   *Nota: O código usa `http://localhost:8000/api` como padrão se a variável `VITE_API_URL` não estiver definida neste arquivo.*

4. Execute o servidor de desenvolvimento:
   ```bash
   npm run dev
   ```

O aplicativo estará disponível em um endereço como http://localhost:5173 (verifique a saída do terminal).

## Executando os Testes (Backend)

1. Certifique-se de estar no diretório raiz do projeto (`voxy/`).
2. Ative o ambiente virtual do backend:
   - Windows: `backend\venv\Scripts\activate`
   - macOS/Linux: `source backend/venv/bin/activate`
3. Execute o Pytest:
   ```bash
   python -m pytest backend
   ```

## Estrutura do Projeto

```
voxy/
├── backend/               # Backend Python com FastAPI
│   ├── app/
│   │   ├── agents/        # Implementações dos agentes e ferramentas
│   │   ├── api/           # Endpoints da API
│   │   ├── core/          # Configurações e componentes centrais
│   │   └── main.py        # Ponto de entrada da aplicação
│   ├── tests/             # Testes unitários
│   ├── .env.example       # Exemplo de variáveis de ambiente
│   └── requirements.txt   # Dependências Python
├── frontend/              # Frontend React com Vite
│   ├── public/
│   ├── src/               # Código fonte do frontend
│   │   ├── components/    # Componentes React
│   │   ├── services/      # Comunicação com API
│   │   └── ...
│   ├── .env.example       # Exemplo de variáveis de ambiente (Vite)
│   ├── index.html
│   ├── package.json       # Dependências Node.js
│   └── vite.config.js
├── memory-bank/           # Documentação interna/contexto para IA
├── docs/                  # Documentação geral do projeto
│   └── ...
├── .gitignore
└── README.md
```

## Contribuindo

Para contribuir com o projeto, consulte os arquivos `PLANNING.md` e `TASK.md` na pasta `docs` para entender a arquitetura, o plano de implementação e as tarefas pendentes.

## Licença

[MIT](LICENSE) 