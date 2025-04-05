/**
 * Serviço para comunicação com a API do backend.
 */

// No Vite, variáveis de ambiente precisam começar com VITE_
// Usamos import.meta.env em vez de process.env
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/**
 * Envia uma mensagem para o agente e retorna a resposta.
 * 
 * @param {string} content - Conteúdo da mensagem
 * @param {string} token - Token de autenticação JWT
 * @returns {Promise<string>} - Resposta do agente
 */
export const sendMessage = async (content, token) => {
  if (!token) {
    return Promise.reject(new Error("Authentication token is missing."));
  }
  
  try {
    const response = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ content }),
    });

    if (!response.ok) {
      let errorDetail = `Error ${response.status}`;
      try {
        const errorData = await response.json();
        errorDetail = errorData.detail || errorDetail;
      } catch (jsonError) {
        // Ignora erro no JSON, errorDetail já tem o status code
      }
      throw new Error(`${errorDetail} (${response.status})`);
    }

    const data = await response.json();
    return data.response;
  } catch (error) {
    console.error('Erro na API (sendMessage):', error);
    throw error; // Re-throw para que o componente possa tratar
  }
};

/**
 * Obtém o histórico de chat (se implementado no backend).
 * 
 * @returns {Promise<Array>} - Lista de mensagens
 */
export const getChatHistory = async () => {
  try {
    const response = await fetch(`${API_URL}/chat/history`);
    
    if (!response.ok) {
      let errorDetail = 'Erro desconhecido ao obter histórico';
       try {
        const error = await response.json();
        errorDetail = error.detail || `Erro ${response.status}`;
      } catch (jsonError) {
        errorDetail = `Erro ${response.status}`;
      }
      throw new Error(errorDetail);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Erro na API (getChatHistory):', error);
    throw error;
  }
};

/**
 * Registra um novo usuário.
 * 
 * @param {string} username - Nome de usuário desejado
 * @param {string} password - Senha desejada
 * @returns {Promise<object>} - Dados do usuário registrado ou objeto de erro
 */
export const registerUser = async (username, password) => {
  try {
    const response = await fetch(`${API_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });

    const data = await response.json(); // Tenta ler JSON mesmo em caso de erro

    if (!response.ok) {
      const errorDetail = data?.detail || `Erro ${response.status} ao registrar`;
      console.error('Erro na API (registerUser):', errorDetail, data);
      throw new Error(errorDetail);
    }

    console.log("Registro bem-sucedido:", data);
    return data; // Retorna os dados do usuário criado (ex: {id, username})
  } catch (error) {
    console.error('Erro geral na API (registerUser):', error);
    // Garante que o erro original seja propagado se for uma instância de Error
    throw error instanceof Error ? error : new Error('Falha no registro.');
  }
};

/**
 * Autentica um usuário e retorna o token de acesso.
 * 
 * @param {string} username - Nome de usuário
 * @param {string} password - Senha
 * @returns {Promise<object>} - Objeto contendo o token de acesso (ex: { access_token: "...", token_type: "bearer" })
 */
export const loginUser = async (username, password) => {
  try {
    // O backend FastAPI com OAuth2PasswordRequestForm espera dados de formulário
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(`${API_URL}/auth/login`, { // Ou /auth/token dependendo da sua rota exata
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });

    const data = await response.json(); // Tenta ler JSON mesmo em caso de erro

    if (!response.ok) {
      const errorDetail = data?.detail || `Erro ${response.status} ao fazer login`;
      console.error('Erro na API (loginUser):', errorDetail, data);
      // Tratar especificamente o erro 401 (Não autorizado)
      if (response.status === 401) {
         throw new Error('Usuário ou senha inválidos.');
      }
      throw new Error(errorDetail);
    }
    
    console.log("Login bem-sucedido, recebido token:", data);
    // Espera-se que o backend retorne { access_token: "...", token_type: "bearer" }
    if (!data.access_token) {
        throw new Error("Token de acesso não recebido do servidor.");
    }
    return data; 
  } catch (error) {
    console.error('Erro geral na API (loginUser):', error);
    // Garante que o erro original seja propagado se for uma instância de Error
    throw error instanceof Error ? error : new Error('Falha no login.');
  }
}; 