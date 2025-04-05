import React, { createContext, useState, useContext, useEffect } from 'react';
import { loginUser as apiLoginUser } from '@/services/api'; // Renomeia para evitar conflito

// 1. Cria o Contexto
const AuthContext = createContext(null);

// 2. Cria o Provedor (AuthProvider)
export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => {
    // Tenta carregar o token do localStorage na inicialização
    try {
      return localStorage.getItem('authToken');
    } catch (error) {
      console.error("Error reading localStorage key \u2018authToken\u2019:", error);
      return null;
    }
  });

  // Efeito para atualizar localStorage quando o token mudar
  useEffect(() => {
    try {
      if (token) {
        localStorage.setItem('authToken', token);
      } else {
        localStorage.removeItem('authToken');
      }
    } catch (error) {
      console.error("Error writing to localStorage key \u2018authToken\u2019:", error);
    }
  }, [token]);

  // Função de Login: chama a API e atualiza o token
  const login = async (username, password) => {
    try {
      const data = await apiLoginUser(username, password);
      if (data.access_token) {
        setToken(data.access_token);
        return data; // Retorna os dados do token em caso de sucesso
      } else {
        // Caso a API retorne sucesso mas sem token (improvável com a validação atual)
        throw new Error('Login successful but no token received.'); 
      }
    } catch (error) {
      console.error('AuthProvider login error:', error);
      setToken(null); // Garante que o token seja limpo em caso de falha
      throw error; // Re-lança o erro para o componente de login tratar
    }
  };

  // Função de Logout: limpa o token
  const logout = () => {
    setToken(null);
    // Opcional: Poderia adicionar uma chamada API para invalidar o token no backend
    console.log("User logged out.");
  };

  // Valor a ser fornecido pelo contexto
  const value = {
    token,
    isAuthenticated: !!token, // Converte o token (string ou null) para boolean
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// 3. Cria um Hook customizado para usar o contexto facilmente
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
} 