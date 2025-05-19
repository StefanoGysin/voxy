import React, { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Paperclip, Image, Send, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Componente de input para envio de mensagens, com suporte para texto,
 * URLs de imagem e upload de arquivos.
 * 
 * @param {Object} props - Propriedades do componente.
 * @param {Function} props.onSendMessage - Callback chamado quando uma mensagem é enviada.
 * @param {boolean} props.disabled - Se o input está desabilitado.
 */
const ChatInput = ({ onSendMessage, disabled = false }) => {
  const [text, setText] = useState('');
  const [isImageUrl, setIsImageUrl] = useState(false);
  const [imageUrl, setImageUrl] = useState('');
  const [isUrlValid, setIsUrlValid] = useState(true);
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  // Validação simples de URL de imagem
  const validateImageUrl = (url) => {
    const pattern = /^https?:\/\/.*\.(jpg|jpeg|png|gif|webp)(\?.*)?$/i;
    return pattern.test(url);
  };

  const handleTextChange = (e) => {
    setText(e.target.value);
  };

  const handleImageUrlChange = (e) => {
    const url = e.target.value;
    setImageUrl(url);
    setIsUrlValid(url === '' || validateImageUrl(url));
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file);
    } else {
      // Limpar seleção se não for imagem
      setSelectedFile(null);
      e.target.value = null;
    }
  };

  const handleSend = (e) => {
    e.preventDefault();
    
    if (disabled) return;
    
    if ((!text.trim() && !imageUrl.trim() && !selectedFile) || 
        (isImageUrl && !isUrlValid)) {
      return; // Não enviar se não houver conteúdo válido
    }
    
    // Estruturar dados para envio
    const messageData = {
      text: text.trim(),
      imageUrl: isImageUrl ? imageUrl.trim() : null,
      file: selectedFile,
    };
    
    // Chamar callback com dados
    onSendMessage(messageData);
    
    // Limpar inputs
    setText('');
    setImageUrl('');
    setSelectedFile(null);
    setIsImageUrl(false);
    
    // Limpar input de arquivo
    if (fileInputRef.current) {
      fileInputRef.current.value = null;
    }
  };

  const toggleImageUrlInput = () => {
    // Alternar entre modo de texto e URL de imagem
    setIsImageUrl(!isImageUrl);
    setImageUrl('');
  };

  const handleFileButtonClick = () => {
    // Trigger click no input de arquivo oculto
    fileInputRef.current?.click();
  };

  // <<< NOVO HANDLER - MODIFICADO >>>
  const handlePaste = (e) => {
    if (disabled) return; // Não fazer nada se estiver desabilitado

    const items = e.clipboardData?.items;
    if (!items) return;

    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf('image') !== -1) {
        const imageFile = items[i].getAsFile();
        if (imageFile) {
          e.preventDefault(); // Prevenir colar texto/base64 no input
          console.log("Image pasted from clipboard, setting as selectedFile:", imageFile);
          
          // Define a imagem colada como o arquivo selecionado
          setSelectedFile(imageFile);
          
          // Limpa outros inputs para focar na imagem colada
          setText('');
          setImageUrl('');
          setIsImageUrl(false);
          if (fileInputRef.current) {
            fileInputRef.current.value = null; // Limpa o input de arquivo caso algo estivesse selecionado
          }
          
          // // REMOVIDO: Não envia mais automaticamente
          // onSendMessage({ file: imageFile }); 
          
          // Opcional: Focar no input de texto para adicionar comentário (requer ref)
          // textInputRef.current?.focus(); 

          break; // Processa apenas o primeiro arquivo de imagem encontrado
        }
      }
    }
  };
  // <<< FIM NOVO HANDLER >>>

  return (
    <form 
      onSubmit={handleSend} 
      className="border-t p-4 flex flex-col space-y-2"
    >
      {/* Mostra preview da imagem selecionada */}
      {selectedFile && (
        <div className="border rounded p-2 flex justify-between items-center bg-muted/20">
          <div className="flex items-center space-x-2">
            <Image className="h-4 w-4" />
            <span className="text-sm truncate max-w-[200px]">{selectedFile.name}</span>
          </div>
          <Button 
            type="button" 
            variant="ghost" 
            size="sm" 
            onClick={() => setSelectedFile(null)}
          >
            Remover
          </Button>
        </div>
      )}
      
      {/* Input alternativo para URL de imagem */}
      {isImageUrl && (
        <div className="flex space-x-2">
          <Input
            type="url"
            placeholder="Cole a URL da imagem aqui..."
            value={imageUrl}
            onChange={handleImageUrlChange}
            disabled={disabled}
            className={cn(!isUrlValid && imageUrl && "border-destructive")}
          />
          <Button 
            type="button" 
            variant="ghost" 
            onClick={() => setIsImageUrl(false)}
          >
            Cancelar
          </Button>
        </div>
      )}
      
      {/* Input principal e botões */}
      <div className="flex items-center space-x-2">
        {/* Input oculto para seleção de arquivo */}
        <input
          type="file"
          accept="image/*"
          className="hidden"
          ref={fileInputRef}
          onChange={handleFileSelect}
          disabled={disabled}
        />
        
        {/* Botão de arquivo */}
        <Button
          type="button"
          variant="ghost"
          size="icon"
          disabled={disabled || isImageUrl}
          onClick={handleFileButtonClick}
          title="Anexar imagem"
        >
          <Paperclip className="h-5 w-5" />
        </Button>
        
        {/* Botão de URL de imagem */}
        <Button
          type="button"
          variant="ghost"
          size="icon"
          disabled={disabled || selectedFile !== null}
          onClick={toggleImageUrlInput}
          title="Adicionar imagem via URL"
        >
          <Image className="h-5 w-5" />
        </Button>
        
        {/* Input de texto - ADICIONADO onPaste */}
        <Input
          type="text"
          placeholder={isImageUrl 
            ? "URL da imagem acima..."
            : selectedFile 
              ? "Adicione um comentário sobre a imagem..."
              : "Digite uma mensagem..."}
          value={text}
          onChange={handleTextChange}
          onPaste={handlePaste}
          disabled={disabled}
        />
        
        {/* Botão de envio */}
        <Button
          type="submit"
          disabled={disabled || 
            ((!text.trim() && !selectedFile && !imageUrl.trim()) || 
             (isImageUrl && !isUrlValid))}
          variant="default"
          size="icon"
        >
          {disabled ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <Send className="h-5 w-5" />
          )}
        </Button>
      </div>
    </form>
  );
};

export default ChatInput; 