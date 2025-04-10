/**
 * Serviço para comunicação com a API do backend.
 */

// No Vite, variáveis de ambiente precisam começar com VITE_
// Usamos import.meta.env em vez de process.env
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'; // Base URL without /api
const AUTH_API_URL = `${API_BASE_URL}/api/auth`; // Auth endpoints live under /api/auth
const API_V1_URL = `${API_BASE_URL}/api/v1/agent`; // V1 agent endpoints live under /api/v1/agent

/**
 * Helper function to handle API responses and errors.
 * @param {Response} response - The fetch response object.
 * @param {string} operationName - Name of the operation for error logging.
 * @returns {Promise<object>} - The JSON data from the response.
 * @throws {Error} - Throws an error if the response is not ok.
 */
const handleApiResponse = async (response, operationName = 'API call') => {
  let data;
  try {
    // Try to parse JSON even if response is not ok, it might contain error details
    data = await response.json();
  } catch (jsonError) {
    // If JSON parsing fails and response is not ok, create a basic error
    if (!response.ok) {
       console.error(`Error in ${operationName}: Failed to parse JSON response for status ${response.status}`);
       throw new Error(`Error ${response.status} in ${operationName}`);
    }
    // If JSON parsing fails but response IS ok, this is unexpected
    console.error(`Error in ${operationName}: Successfully received status ${response.status} but failed to parse JSON response.`);
    throw new Error(`Invalid JSON response received from ${operationName}`);
  }

  if (!response.ok) {
    const errorDetail = data?.detail || `Error ${response.status} during ${operationName}`;
    console.error(`Error in ${operationName}:`, errorDetail, data);
    // Specific handling for common errors if needed
    if (response.status === 401) {
        throw new Error('Unauthorized. Please check your login credentials.');
    }
    if (response.status === 404) {
        throw new Error('Resource not found.');
    }
    throw new Error(errorDetail);
  }

  return data; // Return the parsed JSON data on success
};

/**
 * Registra um novo usuário.
 * 
 * @param {string} username - Nome de usuário desejado
 * @param {string} email - Email desejado
 * @param {string} password - Senha desejada
 * @returns {Promise<object>} - Dados do usuário registrado (ex: {id, username, email})
 */
export const registerUser = async (username, email, password) => {
  try {
    const response = await fetch(`${AUTH_API_URL}/register`, { // Use AUTH_API_URL
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, email, password }), // Include email
    });

    // Use the helper for handling response
    const data = await handleApiResponse(response, 'registerUser');
    console.log("Registro bem-sucedido:", data);
    return data; // Returns UserRead schema {id, username, email}
  } catch (error) {
    // handleApiResponse already logs details, just re-throw
    throw error instanceof Error ? error : new Error('Falha no registro.');
  }
};

/**
 * Autentica um usuário e retorna o token de acesso.
 * 
 * @param {string} email - Email do usuário (usado como username no form)
 * @param {string} password - Senha
 * @returns {Promise<object>} - Objeto contendo o token de acesso (ex: { access_token: "...", token_type: "bearer" })
 */
export const loginUser = async (email, password) => {
  try {
    const formData = new URLSearchParams();
    // Backend expects 'username' in the form for OAuth2PasswordRequestForm
    formData.append('username', email); 
    formData.append('password', password);

    const response = await fetch(`${AUTH_API_URL}/token`, { // Use AUTH_API_URL and /token endpoint
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });

    // Use the helper for handling response
    const data = await handleApiResponse(response, 'loginUser');
    
    console.log("Login bem-sucedido, recebido token:", data);
    if (!data.access_token) {
        throw new Error("Token de acesso não recebido do servidor.");
    }
    return data; 
  } catch (error) {
    // handleApiResponse already logs details, just re-throw
    // Provide a slightly more user-friendly message for auth failures
     if (error.message.includes('Unauthorized') || error.message.includes('401')) {
         throw new Error('Email ou senha inválidos.');
     }
    throw error instanceof Error ? error : new Error('Falha no login.');
  }
};

// --- V1 Agent API Functions ---

/**
 * Busca as sessões de chat do usuário autenticado.
 * @param {string} token - Token de autenticação JWT.
 * @returns {Promise<Array<object>>} - Lista de objetos de sessão (ex: [{id, title, created_at, updated_at}]).
 */
export const getSessions = async (token) => {
  if (!token) {
    return Promise.reject(new Error("Authentication token is missing."));
  }
  try {
    const response = await fetch(`${API_V1_URL}/sessions`, { // Correct: Uses API_V1_URL directly
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    const data = await handleApiResponse(response, 'getSessions');
    // The backend returns { sessions: [...] }, extract the array.
    return data.sessions || [];
  } catch (error) {
    console.error('Erro na API (getSessions):', error);
    throw error;
  }
};

/**
 * Busca as mensagens de uma sessão de chat específica.
 * @param {string} sessionId - O UUID da sessão.
 * @param {string} token - Token de autenticação JWT.
 * @returns {Promise<Array<object>>} - Lista de objetos de mensagem (ex: [{id, session_id, role, content, created_at}]).
 */
export const getSessionMessages = async (sessionId, token) => {
  if (!sessionId || !token) {
    return Promise.reject(new Error("Session ID and authentication token are required."));
  }
  try {
    const response = await fetch(`${API_V1_URL}/sessions/${sessionId}/messages`, { // Correct: Uses API_V1_URL directly
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    const data = await handleApiResponse(response, 'getSessionMessages');
     // The backend returns { messages: [...] }, extract the array.
    return data.messages || [];
  } catch (error) {
    console.error(`Erro na API (getSessionMessages for ${sessionId}):`, error);
    throw error;
  }
};

/**
 * Envia uma nova mensagem para o agente, associada a uma sessão.
 * Se sessionId for null/undefined, uma nova sessão será criada.
 * @param {string} query - A mensagem/pergunta do usuário.
 * @param {string|null} sessionId - O UUID da sessão existente ou null para criar uma nova.
 * @param {string} token - Token de autenticação JWT.
 * @returns {Promise<object>} - Resposta da API (ex: {success, session_id, user_message_id, assistant_message_id}).
 */
export const postChatMessage = async (query, sessionId, token) => {
  if (!query || !token) {
    return Promise.reject(new Error("Query and authentication token are required."));
  }
  try {
    const response = await fetch(`${API_V1_URL}/chat`, { // Correct: Uses API_V1_URL directly
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ query, session_id: sessionId }), // session_id can be null
    });
    const data = await handleApiResponse(response, 'postChatMessage');
    return data; // Returns AgentChatResponse {success, session_id, user_message_id, assistant_message_id}
  } catch (error) {
    console.error('Erro na API (postChatMessage):', error);
    throw error;
  }
};

// Ensure there's no extra code below or the file ends properly.