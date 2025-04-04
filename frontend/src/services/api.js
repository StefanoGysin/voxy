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
 * @returns {Promise<string>} - Resposta do agente
 */
export const sendMessage = async (content) => {
  try {
    const response = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ content }),
    });

    if (!response.ok) {
      let errorDetail = 'Erro desconhecido ao enviar mensagem';
      try {
        const error = await response.json();
        errorDetail = error.detail || `Erro ${response.status}`;
      } catch (jsonError) {
        // Ignora erro ao fazer parse do JSON, usa status code
        errorDetail = `Erro ${response.status}`;
      }
      throw new Error(errorDetail);
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