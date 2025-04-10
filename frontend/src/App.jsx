import React, { useEffect, useRef } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import ChatBox from './components/Chat/ChatBox';
import ChatInput from './components/Chat/ChatInput';
import LoginPage from './pages/Auth/LoginPage';
import RegisterPage from './pages/Auth/RegisterPage';
import { useAuth } from './contexts/AuthContext';
import { useChat } from './contexts/ChatContext';
import { Button } from './components/ui/button';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Terminal } from "lucide-react"
import SessionSidebar from './components/Layout/SessionSidebar';

/**
 * Componente principal da aplicação Voxy.
 * Aplica layout base, roteamento e integra a interface de chat usando ChatContext.
 */
function App() {
  const chatBoxRef = useRef(null);
  const { isAuthenticated, logout } = useAuth();
  const {
    sessions,
    currentSessionId,
    messages,
    isLoadingSessions,
    isLoadingMessages,
    isSendingMessage,
    error,
    sendMessage,
    selectSession,
    createNewSession,
  } = useChat();
  const navigate = useNavigate();

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
        <div className="flex h-screen bg-background text-foreground">
          <SessionSidebar
            sessions={sessions}
            currentSessionId={currentSessionId}
            isLoading={isLoadingSessions}
            onSelectSession={selectSession}
            onCreateNew={createNewSession}
          />
          <div className="flex flex-col flex-1">
            <header className="bg-primary text-primary-foreground p-4 text-lg font-semibold flex justify-between items-center border-b">
              <span>
                {currentSessionId ? `Chat ${currentSessionId.substring(0, 8)}...` : 'Voxy Chat'}
              </span>
              {error && (
                <Alert variant="destructive" className="absolute top-16 left-1/2 transform -translate-x-1/2 w-auto max-w-md z-50">
                  <Terminal className="h-4 w-4" />
                  <AlertTitle>Error</AlertTitle>
                  <AlertDescription>
                    {error}
                  </AlertDescription>
                </Alert>
              )}
              <Button variant="secondary" onClick={() => { logout(); navigate('/login'); }}>Logout</Button>
            </header>
            <main className="flex-1 overflow-hidden">
              <ChatBox messages={messages} chatBoxRef={chatBoxRef} isLoading={isLoadingMessages || (currentSessionId && messages.length === 0)} />
            </main>
            <ChatInput onSendMessage={sendMessage} disabled={isSendingMessage || isLoadingMessages} />
          </div>
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
        element={<ProtectedChatInterface />}
      />

      {/* Redirecionamento para rotas não encontradas */}
      <Route path="*" element={<Navigate to={isAuthenticated ? "/" : "/login"} replace />} />
    </Routes>
  );
}

export default App;
