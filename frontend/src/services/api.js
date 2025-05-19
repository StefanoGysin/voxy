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
 * Sends a chat message (text, optionally with image URL or image path) to the backend.
 * @param {Object} payload - The message payload.
 * @param {string} payload.text - The message text.
 * @param {string|null} payload.sessionId - The current session ID, or null to start a new session.
 * @param {string} payload.token - The user's authentication token.
 * @param {string} [payload.imageUrl] - The URL of an image to send (used if imagePath is not provided).
 * @param {string} [payload.imagePath] - The path of an uploaded image (takes precedence over imageUrl).
 * @returns {Promise<Object>} - A promise that resolves with the backend response (including message IDs, session ID, assistant response).
 * @throws {Error} - Throws an error if the API call fails.
 */
export const postChatMessage = async (payload) => {
  const { text, sessionId, token, imageUrl, imagePath } = payload; // Destructure payload

  if (!token) {
    throw new Error('Authentication token is required to send a message.');
  }

  // Create FormData to handle potential file paths or standard data
  const formData = new FormData();
  formData.append('query', text || ''); // Ensure text is always present, even if empty

  if (sessionId) {
    formData.append('session_id', sessionId);
  }

  // Add image information: prioritize imagePath if available
  if (imagePath) {
    formData.append('image_path', imagePath);
  } else if (imageUrl) {
    formData.append('image_url', imageUrl);
  }

  // Debug: Log FormData contents (won't show file contents, but keys)
  // for (let [key, value] of formData.entries()) {
  //   console.log(`FormData: ${key} = ${value}`);
  // }

  try {
    const response = await fetch(`${API_V1_URL}/chat`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        // Content-Type is set automatically by the browser for FormData
      },
      body: formData, // Send FormData
    });

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch (e) {
        errorData = { detail: response.statusText };
      }
      console.error('Chat API Error:', response.status, errorData);
      throw new Error(errorData.detail || `Failed to send message (${response.status})`);
    }

    return await response.json();

  } catch (error) {
    console.error('Error during chat message fetch:', error);
    // Re-throw the error for the calling context (ChatContext) to handle
    throw error;
  }
};

/**
 * Uploads an image file to the backend.
 * @param {File} file - The image file to upload.
 * @param {string} token - The user's authentication token.
 * @returns {Promise<string>} - A promise that resolves with the image path from the backend.
 * @throws {Error} - Throws an error if the upload fails.
 */
export const uploadImage = async (file, token) => {
  if (!file || !token) {
    throw new Error('File and token are required for upload.');
  }

  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/uploads/image`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        // Content-Type is set automatically by the browser for FormData
      },
      body: formData,
    });

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch (e) {
        // If response is not JSON or empty
        errorData = { detail: response.statusText };
      }
      
      // Melhor log de error para debug
      console.error('Upload API Error:', response.status, errorData);
      
      // Exibir detalhes específicos do erro 422
      if (response.status === 422) {
        console.error('Validation Error Details:', JSON.stringify(errorData));
        // Se for um array de erros, extrair a primeira mensagem
        if (Array.isArray(errorData.detail)) {
          const firstError = errorData.detail[0];
          throw new Error(`Validation error: ${JSON.stringify(firstError)}`);
        }
      }
      
      throw new Error(errorData.detail || `Failed to upload image (${response.status})`);
    }

    const responseJson = await response.json();
    console.log('Upload successful:', responseJson);
    if (!responseJson.image_path) {
        throw new Error('Backend did not return an image_path after upload.');
    }
    return responseJson.image_path;
  } catch (error) {
    console.error('Error during image upload fetch:', error);
    // Re-throw the error to be caught by the calling function (e.g., in ChatContext)
    throw error;
  }
};

// --- Novo Serviço para URL Assinada ---

/**
 * Fetches a short-lived signed URL for a given image path.
 * @param {string} imagePath - The relative path of the image in storage (e.g., 'user_uuid/filename.ext').
 * @param {string} token - The user's authentication token.
 * @returns {Promise<string>} - A promise that resolves with the signed URL string.
 * @throws {Error} - Throws an error if fetching the signed URL fails.
 */
export const getSignedImageUrl = async (imagePath, token) => {
  if (!imagePath || !token) {
    throw new Error('Image path and token are required to get a signed URL.');
  }

  // O endpoint está em /api/v1/uploads/signed-url
  const UPLOAD_API_URL = `${API_BASE_URL}/api/v1/uploads`;

  try {
    // Construir a URL com o path como query parameter
    const url = new URL(`${UPLOAD_API_URL}/signed-url`);
    url.searchParams.append('path', imagePath);

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    const data = await handleApiResponse(response, 'getSignedImageUrl');

    if (!data || !data.signed_url) {
      throw new Error('Signed URL not found in response.');
    }

    return data.signed_url;

  } catch (error) {
    console.error(`Error fetching signed URL for path ${imagePath}:`, error);
    // Re-throw for the component to handle (e.g., show placeholder)
    throw error;
  }
};

// Ensure there's no extra code below or the file ends properly.