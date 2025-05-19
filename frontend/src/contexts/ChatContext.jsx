import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import { supabase } from '../lib/supabaseClient'; // Import supabase client
import { getSessions, getSessionMessages, postChatMessage, uploadImage } from '../services/api';
import { useAuth } from './AuthContext'; // Assuming AuthContext provides the token
import imageCompression from 'browser-image-compression'; // <<< ADICIONAR IMPORT

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
  const [isUploading, setIsUploading] = useState(false); // Estado para upload
  const [isCompressing, setIsCompressing] = useState(false); // <<< ADICIONAR ESTADO PARA COMPRESSÃO
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
  const sendMessage = useCallback(async (messageData) => {
    // Agora recebe text, imageUrl, e file
    const { text, imageUrl, file } = messageData;

    // Verifica se há algo para enviar
    if (!token || (!text?.trim() && !imageUrl?.trim() && !file)) return;

    setIsSendingMessage(true);
    setIsUploading(!!file); // Define uploading se houver um arquivo
    setIsCompressing(false); // Reseta compressing state
    setError(null);

    const optimisticMessageId = `optimistic-${Date.now()}`;
    let optimisticImageUrl = null;
    let objectUrlToRevoke = null; // Para limpar URL de objeto
    let fileToUpload = file; // Usará o arquivo original ou o comprimido
    let uploadError = null;

    // <<< INÍCIO: LÓGICA DE COMPRESSÃO >>>
    if (file) {
      const options = {
        maxSizeMB: 4.5, // Nosso limite da API é 5MB, definimos um pouco menos
        maxWidthOrHeight: 1920, // Redimensiona se for maior que Full HD
        useWebWorker: true, // Usa Web Worker para não bloquear a thread principal
        // initialQuality: 0.7 // Pode ajustar a qualidade se necessário
      };

      // Verifica se precisa comprimir
      if (file.size > options.maxSizeMB * 1024 * 1024) {
        console.log(`Original file size: ${(file.size / 1024 / 1024).toFixed(2)} MB. Compressing...`);
        setIsCompressing(true); // Indica que a compressão começou
        try {
          fileToUpload = await imageCompression(file, options);
          console.log(`Compressed file size: ${(fileToUpload.size / 1024 / 1024).toFixed(2)} MB`);
        } catch (compressionError) {
          console.error("Image compression failed:", compressionError);
          setError('Failed to compress image. Please try a smaller file.');
          setIsSendingMessage(false);
          setIsUploading(false);
          setIsCompressing(false);
          return; // Interrompe o envio se a compressão falhar
        } finally {
           setIsCompressing(false); // Indica que a compressão terminou (sucesso ou falha)
        }
      } else {
         console.log(`File size is within limits: ${(file.size / 1024 / 1024).toFixed(2)} MB. No compression needed.`);
      }
       // Cria URL de objeto APÓS a possível compressão
      optimisticImageUrl = URL.createObjectURL(fileToUpload);
      objectUrlToRevoke = optimisticImageUrl;
      console.log("Created Object URL:", optimisticImageUrl);
    } else if (imageUrl) {
      optimisticImageUrl = imageUrl; // Usar a URL fornecida
    }
    // <<< FIM: LÓGICA DE COMPRESSÃO >>>


    // Adiciona mensagem otimista (usando a URL do arquivo original ou comprimido)
    const userMessage = {
      id: optimisticMessageId,
      session_id: currentSessionId, // Might be null if new session
      role: 'user',
      content: text || '', // Use text or empty string
      // Usar a URL otimista (objeto ou fornecida) ou null
      image_url: optimisticImageUrl,
      created_at: new Date().toISOString(),
      // Poderíamos adicionar um status de envio aqui, se necessário
      // status: file ? (isCompressing ? 'compressing' : 'uploading') : 'sending', // Exemplo de status
    };
    setMessages(prevMessages => [...prevMessages, userMessage]);


    let imagePath = null;
    // Nenhuma mudança necessária aqui, uploadError já está definido fora do bloco de compressão

    try {
      // 1. Fazer upload se houver arquivo (original ou comprimido)
      if (fileToUpload) { // <<< USA fileToUpload AQUI >>>
        setIsUploading(true); // Garante que isUploading esteja true aqui
        try {
          imagePath = await uploadImage(fileToUpload, token); // <<< USA fileToUpload AQUI >>>
          // Atualizar status otimista (opcional)
          // setMessages(prev => prev.map(msg => msg.id === optimisticMessageId ? { ...msg, status: 'sending' } : msg));
        } catch (err) {
          console.error("Upload failed:", err);
          uploadError = err; // Armazenar erro de upload
          // Não joga o erro aqui ainda, vamos tentar postar sem imagem se houver texto
          // throw err; // Joga erro para o catch principal se upload for essencial
        } finally {
          setIsUploading(false); // Upload terminou (sucesso ou falha)
        }
      }

      // Se houve erro no upload E não há texto, falha total
      if (uploadError && !text?.trim()) {
         throw uploadError; // Propaga o erro de upload
      }

      // 2. Enviar mensagem para a API de chat
      // Precisamos garantir que postChatMessage aceite imagePath e o envie como image_path
      // Por agora, vamos passar como está, assumindo que postChatMessage será adaptado
      const payload = {
          text: text || '', // Enviar texto vazio se não houver
          sessionId: currentSessionId,
          token: token,
          // Passa imagePath OU imageUrl, dando preferência ao path se upload ocorreu
          imagePath: imagePath, // Nova propriedade esperada por postChatMessage?
          imageUrl: imagePath ? null : imageUrl, // Ou envia apenas um deles?
          // --> VAMOS ASSUMIR QUE postChatMessage aceita { text, imagePath, imageUrl, sessionId, token }
          // --> E que ele prioriza imagePath se ambos forem fornecidos (ou lida com isso de alguma forma)
      }
      const result = await postChatMessage(payload); // Passar o payload

      // Adicionar logs detalhados para depuração
      console.log("Chat API Response (detalhado):", {
        success: result.success,
        session_id: result.session_id,
        user_message_id: result.user_message_id,
        user_message: result.user_message, // Verificar se isso está vindo com a URL da imagem
        assistant_content: result.assistant_content?.substring(0, 50) + "..." // Truncado para legibilidade
      });
      
      // Se era nova sessão, atualiza ID e busca sessões
      if (!currentSessionId && result.session_id) {
        setCurrentSessionId(result.session_id);
        fetchSessions(); // Refresh session list
      }

      // Atualiza mensagem otimista com dados reais vindos do backend
      setMessages(prevMessages =>
        prevMessages.map(msg =>
          // Encontra a mensagem otimista pelo ID temporário
          msg.id === optimisticMessageId
            // Substitui a mensagem otimista pelos dados completos recebidos em result.user_message
            // result.user_message já contém id, session_id, role, content, created_at, metadata, e image_path
            ? { 
                ...result.user_message, // Usa o objeto completo retornado pela API
                // Garante que o ID final seja usado (embora já deva estar correto em user_message)
                id: result.user_message_id 
              } 
            : msg // Mantém as outras mensagens como estão
        )
      );
      
      // Adiciona a mensagem do assistente (se houver na resposta direta)
      if (result.success && result.assistant_content && result.assistant_message_id) {
         // ... (lógica existente para adicionar mensagem do assistente, verificar duplicatas, ordenar) ...
         // IMPORTANTE: A mensagem do assistente pode conter a análise da imagem.
         // A `image_url` na mensagem do *usuário* deve ser a URL assinada da imagem enviada.
        const assistantMessage = {
          id: result.assistant_message_id,
          session_id: result.session_id,
          role: 'assistant',
          content: result.assistant_content,
          // A resposta do assistente pode ter uma URL de imagem?
          // Por exemplo, se pedirmos para gerar uma imagem?
          // Por enquanto, vamos assumir que não.
          image_url: result.assistant_message?.image_url || null, 
          created_at: new Date().toISOString(), 
        };
        setMessages(prevMessages => {
            const messageExists = prevMessages.some(msg => msg.id === assistantMessage.id);
            if (!messageExists) {
                 const updatedMessages = [...prevMessages, assistantMessage];
                 updatedMessages.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
                 return updatedMessages;
            }
            return prevMessages;
        });
      }

    } catch (err) {
      console.error("Failed to send message or upload:", err);
      // Usar a mensagem de erro do upload se foi esse o problema
      setError(uploadError?.message || err.message || 'Failed to send message. Please try again.');
      // Remove optimistic message on failure
      setMessages(prevMessages => prevMessages.filter(msg => msg.id !== optimisticMessageId));
    } finally {
      setIsSendingMessage(false);
      // setIsUploading já é tratado no bloco try/catch/finally do upload
      // isCompressing já é tratado no bloco try/catch/finally da compressão
      // Revoga a URL do objeto para liberar memória
      if (objectUrlToRevoke) {
        console.log("Revoking Object URL:", objectUrlToRevoke);
        URL.revokeObjectURL(objectUrlToRevoke);
      }
    }
  }, [token, currentSessionId, fetchSessions]); // Removido uploadImage daqui, adicionado fetchSessions se necessário

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
    isUploading, // Passar estado de upload
    isCompressing, // <<< PASSAR ESTADO DE COMPRESSÃO >>>
    error,
    fetchSessions,
    selectSession,
    createNewSession,
    sendMessage,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
};

export default ChatProvider; // Ensure default export if used elsewhere 