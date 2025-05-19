import React, { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check, Image, ImageOff, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { getSignedImageUrl } from '@/services/api';

/**
 * Componente que renderiza uma mensagem individual do chat.
 * Suporta mensagens do usuário e do assistente, com ou sem imagens.
 * Renderiza conteúdo Markdown, destaca blocos de código e adiciona botões de cópia.
 * Busca URL assinada para imagens sob demanda se message.image_path estiver presente.
 * 
 * @param {Object} props - Propriedades do componente.
 * @param {Object} props.message - Objeto de mensagem com id, role, content e image_path.
 */
const ChatMessage = ({ message }) => {
  const isUser = message.role === 'user';
  const [copiedMessage, setCopiedMessage] = useState(false);
  const [displayImageUrl, setDisplayImageUrl] = useState(null);
  const [imageLoadingState, setImageLoadingState] = useState('idle');
  
  const { token } = useAuth();

  const copyToClipboard = (text, setCopiedState) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedState(true);
      setTimeout(() => setCopiedState(false), 2000);
    }).catch(err => {
      console.error('Failed to copy text: ', err);
    });
  };

  useEffect(() => {
    setCopiedMessage(false);
    
    console.log(`[ChatMessage ${message.id}] Received message:`, message);
    if (message.image_path && token) {
      console.log(`[ChatMessage ${message.id}] Has image_path: ${message.image_path}. Fetching URL...`);
      setImageLoadingState('loading');
      setDisplayImageUrl(null);

      getSignedImageUrl(message.image_path, token)
        .then(signedUrl => {
          console.log(`[ChatMessage ${message.id}] Successfully fetched signed URL.`);
          setDisplayImageUrl(signedUrl);
          setImageLoadingState('idle');
        })
        .catch(error => {
          console.error(`[ChatMessage ${message.id}] Failed to fetch signed URL:`, error);
          setDisplayImageUrl(null);
          setImageLoadingState('error');
        });
    } else {
      console.log(`[ChatMessage ${message.id}] No image_path or no token.`);
      setDisplayImageUrl(null);
      setImageLoadingState('idle');
    }
    
  }, [message.id, message.image_path, token]);

  const CodeBlock = ({ node, inline, className, children, ...props }) => {
    const [copiedCode, setCopiedCode] = useState(false);
    const match = /language-(\\w+)/.exec(className || '');
    const language = match ? match[1] : null;
    const codeText = String(children).replace(/\\n$/, '');

    const handleCopyCode = () => {
      copyToClipboard(codeText, setCopiedCode);
    };

    return !inline && language ? (
      <div className="relative group my-2">
        <SyntaxHighlighter
          style={vscDarkPlus}
          language={language}
          PreTag="div"
          {...props}
        >
          {codeText}
        </SyntaxHighlighter>
        <Button 
          variant="ghost" 
          size="icon" 
          className="absolute top-2 right-2 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={handleCopyCode}
          aria-label="Copiar código"
        >
          {copiedCode ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
        </Button>
      </div>
    ) : !inline ? (
      <div className="relative group my-2">
        <pre className="bg-gray-800 text-white p-4 rounded overflow-x-auto" {...props}>
          <code>{children}</code>
        </pre>
        <Button 
          variant="ghost" 
          size="icon" 
          className="absolute top-2 right-2 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={handleCopyCode}
          aria-label="Copiar código"
        >
          {copiedCode ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
        </Button>
      </div>
    ) : (
      <code className={cn("bg-muted px-1 py-0.5 rounded text-sm", className)} {...props}>
        {children}
      </code>
    );
  };

  const handleCopyMessage = () => {
    copyToClipboard(message.content, setCopiedMessage);
  };

  return (
    <div className="group relative">
      <div
        className={cn(
          'flex flex-col max-w-[80%] rounded-lg p-4 mb-2',
          isUser 
            ? 'bg-primary text-primary-foreground self-end' 
            : 'bg-muted self-start'
        )}
      >
        <div className="flex justify-between items-center mb-1">
          <div className="text-xs opacity-70">
            {isUser ? 'Você' : 'Voxy'}
          </div>
          
          <Button 
            variant="ghost" 
            size="icon" 
            className="h-5 w-5 opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={handleCopyMessage}
            aria-label="Copiar mensagem"
          >
            {copiedMessage ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
          </Button>
        </div>
        
        {message.image_path && (
          <div className="mt-2 mb-2 max-w-full min-h-[50px] flex items-center justify-center bg-muted/50 rounded-md">
            {imageLoadingState === 'loading' && (
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            )}
            {imageLoadingState === 'error' && (
              <div className="flex flex-col items-center text-destructive text-xs p-2">
                <ImageOff className="h-5 w-5 mb-1"/>
                <span>Falha ao carregar</span>
              </div>
            )}
            {imageLoadingState === 'idle' && displayImageUrl && (
              console.log(`[ChatMessage ${message.id}] Rendering image with URL:`, displayImageUrl),
              <img 
                src={displayImageUrl} 
                alt="Imagem enviada" 
                className="max-w-full rounded-md max-h-[300px] object-contain"
              />
            )}
          </div>
        )}
        
        <div className={cn(
          "prose prose-sm dark:prose-invert max-w-none break-words",
          isUser ? "prose-p:text-primary-foreground prose-li:text-primary-foreground prose-strong:text-primary-foreground prose-em:text-primary-foreground prose-a:text-primary-foreground prose-blockquote:text-primary-foreground prose-code:text-primary-foreground" : "",
        )}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              code: CodeBlock,
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
};

export default ChatMessage; 