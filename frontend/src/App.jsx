import React, { useState, useEffect, useRef } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'; // Added useNavigate
import ChatBox from './components/Chat/ChatBox';
import ChatInput from './components/Chat/ChatInput';
import { sendMessage } from './services/api'; // Assuming you have this service
import LoginPage from './pages/Auth/LoginPage'; // Import Login Page
import RegisterPage from './pages/Auth/RegisterPage'; // Import Register Page
import { useAuth } from './contexts/AuthContext'; // Import useAuth
import { Button } from './components/ui/button'; // For Logout Button

/**
 * Componente principal da aplicação Voxy.
 * Aplica layout base, roteamento e integra o ChatBox.
 */
function App() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const chatBoxRef = useRef(null);
  const { isAuthenticated, logout, token } = useAuth(); // Use context values
  const navigate = useNavigate(); // For logout navigation

  const handleSendMessage = async (inputValue) => {
    if (!inputValue.trim()) return;
    if (!token) { // Verifica se há token antes de enviar
        console.error("No auth token found. Please login again.");
        logout(); // Desloga se não houver token
        return;
    }

    const userMessage = { role: 'user', content: inputValue };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setIsLoading(true);

    try {
      // TODO: Update sendMessage in api.js to actually use the token
      const botResponseContent = await sendMessage(inputValue, token); // Passa o token
      const botMessage = { role: 'assistant', content: botResponseContent };
      setMessages((prevMessages) => [...prevMessages, botMessage]);
    } catch (error) {
      console.error("Failed to send message:", error);
      // Se o erro for 401 (Unauthorized), desloga o usuário
      if (error.message && error.message.includes("401")) { 
          logout();
          navigate('/login'); // Redireciona para login
          setMessages((prevMessages) => [
              ...prevMessages,
              { role: 'assistant', content: 'Session expired. Please login again.' }
          ]);
      } else {
          const errorMessageContent = `Error: ${error.message || 'Could not connect to the server.'}`;
          const errorMessage = { role: 'assistant', content: errorMessageContent };
          setMessages((prevMessages) => [...prevMessages, errorMessage]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Auto-scroll to bottom
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [messages]);

  // Componente para a interface de Chat protegida
  const ProtectedChatInterface = () => {
      // Se não estiver autenticado, navega para login (double check)
      if (!isAuthenticated) {
          return <Navigate to="/login" replace />;
      }
      
      return (
        <div className="flex flex-col h-screen bg-background text-foreground">
          <header className="bg-primary text-primary-foreground p-4 text-center text-lg font-semibold flex justify-between items-center">
            <span>Voxy Chat</span>
            <Button variant="destructive" onClick={() => { logout(); navigate('/login'); }}>Logout</Button>
          </header>
          <main className="flex-1 overflow-hidden">
            <ChatBox messages={messages} chatBoxRef={chatBoxRef} />
          </main>
          <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
        </div>
      );
  };

  return (
    <Routes>
      {/* Rotas públicas */}
      <Route 
        path="/login" 
        element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />} 
      />
      <Route 
        path="/register" 
        element={isAuthenticated ? <Navigate to="/" replace /> : <RegisterPage />} 
      />
      
      {/* Rota protegida */}
      <Route 
        path="/"
        element={<ProtectedChatInterface />} // Usa o componente protegido
      />
      
      {/* Redirecionamento para rotas não encontradas */}
      <Route path="*" element={<Navigate to={isAuthenticated ? "/" : "/login"} replace />} />
    </Routes>
  );
}

export default App;
