import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import { supabase } from '../lib/supabaseClient'; // Import supabase client
import { getSessions, getSessionMessages, postChatMessage } from '../services/api';
import { useAuth } from './AuthContext'; // Assuming AuthContext provides the token

const ChatContext = createContext();

export const useChat = () => useContext(ChatContext);

export const ChatProvider = ({ children }) => {
  const { token, isAuthenticated } = useAuth(); // Get token from AuthContext
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isSendingMessage, setIsSendingMessage] = useState(false);
  const [error, setError] = useState(null);

  // Fetch sessions when user is authenticated and token is available
  const fetchSessions = useCallback(async () => {
    if (!token) return;
    setIsLoadingSessions(true);
    setError(null);
    try {
      const fetchedSessions = await getSessions(token);
      // Sort sessions by updated_at descending (most recent first)
      fetchedSessions.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
      setSessions(fetchedSessions);
    } catch (err) {
      console.error("Failed to fetch sessions:", err);
      setError('Failed to load chat sessions.');
      setSessions([]); // Clear sessions on error
    } finally {
      setIsLoadingSessions(false);
    }
  }, [token]);

  // Select a session and load its messages
  const selectSession = useCallback(async (sessionId) => {
    if (!token || !sessionId) return;
    if (sessionId === currentSessionId) return; // Avoid reloading the same session

    setCurrentSessionId(sessionId);
    setMessages([]); // Clear previous messages
    setIsLoadingMessages(true);
    setError(null);
    try {
      const fetchedMessages = await getSessionMessages(sessionId, token);
       // Sort messages by created_at ascending (oldest first)
      fetchedMessages.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
      setMessages(fetchedMessages);
    } catch (err) {
      console.error(`Failed to fetch messages for session ${sessionId}:`, err);
      setError('Failed to load messages for this session.');
      setMessages([]); // Clear messages on error
    } finally {
      setIsLoadingMessages(false);
    }
  }, [token, currentSessionId]); // Added currentSessionId to dependencies

  // Function to start a new chat (clears current selection)
  const createNewSession = () => {
    setCurrentSessionId(null);
    setMessages([]);
    setError(null);
  };

  // Send a message (either to current session or starts a new one)
  const sendMessage = useCallback(async (query) => {
    if (!token || !query.trim()) return;

    setIsSendingMessage(true);
    setError(null);

    const optimisticMessageId = `optimistic-${Date.now()}`;
    // Optimistically add user message
    const userMessage = {
      id: optimisticMessageId,
      session_id: currentSessionId, // Might be null if new session
      role: 'user',
      content: query,
      created_at: new Date().toISOString(),
    };
    setMessages(prevMessages => [...prevMessages, userMessage]);

    try {
      // The API call returns the actual session_id and message IDs
      const result = await postChatMessage(query, currentSessionId, token);
      console.log("API Response:", result);

      // If it was a new session, update the currentSessionId and refetch sessions
      if (!currentSessionId && result.session_id) {
        setCurrentSessionId(result.session_id);
        fetchSessions(); // Refresh session list to show the new one
      }

      // Update the optimistic message with the real ID from the backend response (if needed)
      // Or simply rely on the Realtime update to correct the state
      setMessages(prevMessages =>
        prevMessages.map(msg =>
          msg.id === optimisticMessageId
            ? { ...msg, id: result.user_message_id, session_id: result.session_id } // Update ID and session_id
            : msg
        )
      );

      // Assistant message will likely arrive via Realtime subscription
      // We might add a placeholder here if needed, or wait for Realtime
      if (result.success && result.assistant_content && result.assistant_message_id) {
        const assistantMessage = {
          id: result.assistant_message_id,
          session_id: result.session_id,
          role: 'assistant',
          content: result.assistant_content,
          created_at: new Date().toISOString(), // Usar tempo atual ou backend se disponível
        };
        // Adiciona a mensagem do assistente ao estado, garantindo que não haja duplicatas se o Realtime chegar rápido
        setMessages(prevMessages => {
            const messageExists = prevMessages.some(msg => msg.id === assistantMessage.id);
            if (!messageExists) {
                 const updatedMessages = [...prevMessages, assistantMessage];
                 // Reordenar após adicionar, caso necessário (embora map + sort possa ser mais eficiente)
                 updatedMessages.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
                 return updatedMessages;
            }
            return prevMessages; // Retorna o estado anterior se a mensagem já existe
        });
      }

    } catch (err) {
      console.error("Failed to send message:", err);
      setError('Failed to send message. Please try again.');
      // Remove optimistic message on failure
      setMessages(prevMessages => prevMessages.filter(msg => msg.id !== optimisticMessageId));
    } finally {
      setIsSendingMessage(false);
    }
  }, [token, currentSessionId, fetchSessions]); // Added fetchSessions dependency

  // Effect to fetch sessions when authenticated
  useEffect(() => {
    if (isAuthenticated && token) {
      fetchSessions();
    } else {
      // Clear state if user logs out
      setSessions([]);
      setCurrentSessionId(null);
      setMessages([]);
      setError(null);
    }
  }, [isAuthenticated, token, fetchSessions]);

  // TODO: Implement Realtime subscription using Supabase
  useEffect(() => {
    if (!currentSessionId || !supabase) return;

    console.log(`Subscribing to messages for session: ${currentSessionId}`);

    const channel = supabase
      .channel(`messages:session_id=eq.${currentSessionId}`)
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'messages', filter: `session_id=eq.${currentSessionId}` },
        (payload) => {
          console.log('New message received:', payload.new);
          // Ensure the message isn't already present (e.g., from optimistic update)
          // Especially check for assistant messages
          if (payload.new && payload.new.role === 'assistant') {
             // Sort messages by created_at ascending (oldest first) after adding
            setMessages(prevMessages => {
              // Avoid duplicates
              if (prevMessages.some(msg => msg.id === payload.new.id)) {
                return prevMessages;
              }
              const updatedMessages = [...prevMessages, payload.new];
              updatedMessages.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
              return updatedMessages;
            });
          }
        }
      )
      .subscribe((status, err) => {
        if (status === 'SUBSCRIBED') {
          console.log(`Successfully subscribed to session ${currentSessionId}`);
        } else if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT') {
           console.error(`Subscription error for session ${currentSessionId}:`, status, err);
           setError('Realtime connection error. Chat updates may be delayed.');
        }
      });

    // Cleanup function to unsubscribe when component unmounts or session changes
    return () => {
      console.log(`Unsubscribing from session: ${currentSessionId}`);
      supabase.removeChannel(channel);
    };
  }, [currentSessionId]); // Depend on currentSessionId


  const value = {
    sessions,
    currentSessionId,
    messages,
    isLoadingSessions,
    isLoadingMessages,
    isSendingMessage,
    error,
    fetchSessions,
    selectSession,
    createNewSession,
    sendMessage,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}; 