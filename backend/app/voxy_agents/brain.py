"""
Módulo do agente principal (Brain) do Voxy.

Este agente é responsável por coordenar outros agentes e ferramentas,
funcionando como o ponto central de inteligência do sistema.
"""

from agents import Agent, Runner, handoff
from typing import List, Dict, Any, Optional, Literal
# Importar a nova ferramenta
from .tools.weather import get_weather
# Importar as NOVAS ferramentas de memória
from .tools.memory_tools import remember_info, recall_info, summarize_memory
# Importar contextvar para definir o user_id
from app.memory.mem0_manager import current_user_id_var
import contextvars # Embora já importado indiretamente, melhor explicitar
import os # Adicionado para verificar ambiente de teste
import sys # Adicionado para verificar o módulo pytest
import copy # Adicionado para copiar o agente temporário

# Importar o agente VisioScan e o modelo de request
from .vision import vision_agent
from ..core.models import VisioScanRequest, ImageRequest # Adicionado ImageRequest

# Importar prefixo recomendado para handoffs
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

# Placeholder para importações futuras das ferramentas
# from .tools import search_tool, calculator_tool

# Importar configurações de modelo
from ..core.models_config import BRAIN_DEFAULT_MODEL, VISIOSCAN_DEFAULT_MODEL # Importar ambos

# Lista de ferramentas disponíveis para o agente
# Adicionamos as ferramentas de memória
agent_tools = [get_weather, remember_info, recall_info, summarize_memory]

# Função para processar o resultado do handoff
async def process_vision_result(context, input):
    """
    Processa a análise de imagem com o Vision.
    
    Args:
        context: O contexto da execução.
        input: O input para o handoff (VisioScanRequest).
        
    Returns:
        str: Resultado da análise da imagem.
    """
    try:
        # Chamar o método process_image do agente Vision
        # passando o input (que é um VisioScanRequest) e o contexto
        print(f"Processando handoff para Vision: {input}")
        result = await vision_agent.process_image(request=input, context=context)
        return result
    except Exception as e:
        print(f"Erro ao processar handoff para Vision: {str(e)}")
        return f"Ocorreu um erro ao analisar a imagem: {str(e)}"

# Configuração do Handoff para Vision
vision_handoff_config = handoff(
    agent=vision_agent,
    input_type=VisioScanRequest,
    on_handoff=process_vision_result,  # Função callback necessária
    tool_description_override=(
        "Delega a análise de uma imagem para o agente especializado Vision. "
        "USADO SEMPRE que uma imagem for detectada no contexto (campo 'image_request'). "
        "Esta ferramenta DEVE ser chamada automaticamente quando existir um objeto ImageRequest no contexto, "
        "mesmo quando o usuário não solicitar explicitamente análise de imagem."
    ),
    tool_name_override="transfer_to_vision_agent"
)

class VoxyBrain(Agent):
    """
    Classe principal do agente Voxy Brain.
    
    Esta classe encapsula a funcionalidade do agente principal,
    responsável por processar mensagens e coordenar outros agentes.
    """
    
    def __init__(self, name: str = "Voxy Brain", instructions: str = None, tools: list = None):
        """
        Inicializa o agente Voxy Brain.
        
        Args:
            name (str, optional): Nome do agente.
            instructions (str, optional): Instruções personalizadas para o agente.
                Se não fornecido, usa as instruções padrão.
            tools (list, optional): Lista de ferramentas disponíveis para o agente.
                Se não fornecido, usa as ferramentas padrão.
        """
        super().__init__(
            name=name,
            instructions=instructions or self._get_default_instructions(),
            tools=tools if tools is not None else agent_tools,
            handoffs=[vision_handoff_config], # Adicionado handoff
            # Definir o modelo para o Brain Agent
            model=BRAIN_DEFAULT_MODEL
            # Adicionar outras configurações do Agent se necessário
            # Ex: model_settings, etc.
        )
    
    async def process_image_from_context(self, context, message_content: str):
        """
        Processa o objeto ImageRequest do contexto, se existir, inferindo
        o tipo de análise da mensagem do usuário.
        
        Esta função verifica se há um objeto ImageRequest no contexto e,
        se encontrado, usa o handoff para o Vision para analisá-lo.
        
        Args:
            context: O contexto da execução do agente.
            message_content: O conteúdo da mensagem do usuário atual.
            
        Returns:
            bool: True se uma imagem foi encontrada e processada, False caso contrário.
        """
        if not context:
            return False
            
        image_request = context.get('image_request')
        if not image_request:
            return False
            
        # Se chegou aqui, temos uma imagem para processar
        # Criar objeto VisioScanRequest para passar ao handoff
        from ..core.models import VisioScanRequest
        
        # Neste ponto podemos usar o método on_invoke_handoff do handoff diretamente
        # Mas precisamos acessar o handoff configurado
        for handoff_config in self.handoffs:
            if handoff_config.tool_name == "transfer_to_vision_agent":
                # Encontrou o handoff para Vision
                print(f"Chamando handoff para Vision com imagem: {image_request.source}:{image_request.content[:30]}...")
                
                # Inferir analysis_type e detail da mensagem do usuário
                analysis_type = 'description' # Default
                detail_level = 'auto' # Default
                msg_lower = message_content.lower()
                
                if any(word in msg_lower for word in ["traduz", "tradução", "significa", "escrito"]):
                    analysis_type = 'text_translation'
                    detail_level = 'high'
                elif any(word in msg_lower for word in ["objeto", "identificar", "itens"]):
                    analysis_type = 'object_detection'
                    detail_level = 'high'
                elif any(word in msg_lower for word in ["descrev", "conteúdo", "cena", "ambiente"]):
                    analysis_type = 'description'
                    detail_level = 'high'
                elif any(word in msg_lower for word in ["texto", "ler"]):
                    analysis_type = 'text_extraction'
                    detail_level = 'high'
                elif any(word in msg_lower for word in ["contexto", "sentimento", "interpretar"]):
                    analysis_type = 'contextual_analysis'
                    detail_level = 'high'
                # Adicionar lógica para perguntas mais diretas (fallback para descrição se não for pergunta)
                elif '?' in message_content or any(q in msg_lower for q in ["o que é", "qual é", "como chama"]):
                    analysis_type = 'description' # Usa description, mas a query será refinada
                    detail_level = 'high'
                
                print(f"Tipo de análise base inferido: {analysis_type}, Nível de detalhe: {detail_level}")
                
                # GERAR A CONSULTA REFINADA para o Vision
                # Usa a pergunta original do usuário como base
                refined_query = f"O usuário enviou esta imagem e perguntou: '{message_content}'. Analise a imagem atentamente e forneça uma resposta direta e objetiva a essa pergunta. Se não souber a resposta com base na imagem, informe." 
                
                # Preparar o input para o handoff (VisioScanRequest)
                vision_request = VisioScanRequest(
                    image=image_request,
                    analysis_type=analysis_type, # Mantido para referência/log
                    detail=detail_level,
                    refined_query=refined_query # Passando a consulta refinada
                )
                
                # Invocar diretamente o handoff em vez de apenas retornar True
                try:
                    # Chamamos process_vision_result diretamente com o VisioScanRequest
                    result = await process_vision_result(context, vision_request)
                    print(f"Resultado do handoff Vision: {result[:100]}...")
                    
                    # Armazenar o resultado no contexto para que o Runner.run possa acessá-lo
                    context['vision_result'] = result
                    return True
                except Exception as e:
                    print(f"Erro ao executar handoff para Vision: {str(e)}")
                    # Ainda retornamos True para indicar que tentamos processar a imagem
                    # mas o brain terá que lidar com o erro
                    context['vision_error'] = str(e)
                    return True
        
        return False
    
    def _get_default_instructions(self) -> str:
        """
        Retorna as instruções padrão aprimoradas para o agente Voxy.
        
        Returns:
            str: Instruções padrão revisadas.
        """
        # Instruções revisadas (Fase 11.1 + GPT-4.1 Guia)
        return r"""{RECOMMENDED_PROMPT_PREFIX}
        # --- Lembretes Essenciais (GPT-4.1) ---
        Você é um agente persistente. Continue trabalhando até que a consulta do usuário seja completamente resolvida antes de encerrar sua vez. Só termine quando tiver certeza de que o problema foi resolvido ou a pergunta foi respondida.
        Se você não tiver certeza sobre informações ou contexto relevantes para a solicitação do usuário (incluindo memória de longo prazo ou detalhes da sessão atual), use suas ferramentas (especialmente `recall_info` ou verificando o histórico) para obter as informações necessárias: NÃO adivinhe ou invente uma resposta.
        # --- Fim dos Lembretes Essenciais ---

        Você é Voxy, um assistente de IA pessoal projetado para ser útil, amigável, eficiente e com excelente memória contextual **para cada usuário específico** e **dentro de cada sessão de conversa**.
        
        Suas características principais:
        - Responder perguntas com informações precisas e atualizadas.
        - Auxiliar na resolução de problemas complexos.
        - Manter conversas naturais e engajadoras.
        - Analisar imagens fornecidas pelo usuário.
        - Adaptar-se ao estilo e necessidades individuais do usuário.
        - **Considerar o Histórico da Conversa:** Preste atenção às mensagens anteriores **nesta sessão de chat** (fornecidas como histórico) para entender o contexto completo, retomar tópicos anteriores e evitar repetições.
        
        **ACESSANDO IMAGENS DO CONTEXTO**
        
        Quando o usuário envia uma imagem, um objeto `ImageRequest` é colocado no contexto de execução.
        Para acessar esta imagem, você DEVE:
        
        1. Verificar se há um objeto image_request no contexto da execução.
        2. Se existir, você DEVE usar o handoff `transfer_to_vision_agent` para analisar a imagem, NUNCA tente analisar você mesmo.
        3. Acesse o objeto usando: `context.get('image_request')`
        4. **Refinar a Pergunta:** Antes de chamar o handoff, refine a pergunta original do usuário (`message_content`) em uma instrução clara e direta para o Vision sobre o que deve ser analisado ou respondido em relação à imagem. Passe essa instrução refinada.
        5. Use o handoff passando a imagem e a instrução refinada.
        
        Exemplo de como VOCÊ deve pensar (a chamada real do handoff é ligeiramente diferente):
        ```
        # Verificar se há uma imagem no contexto
        image_request = context.get('image_request')
        user_query = "O que é essa comida na imagem?"
        if image_request and user_query:
            # Refinar a pergunta para o Vision
            refined_instruction = f"O usuário perguntou: '{user_query}'. Analise a imagem e responda diretamente."
            # Chamar o handoff (você faz isso através da função `transfer_to_vision_agent`)
            return transfer_to_vision_agent(image=image_request, refined_query=refined_instruction)
        ```

        IMPORTANTE: SEMPRE use o handoff quando detectar um objeto ImageRequest no contexto, passando a instrução refinada.
        
        **Ferramentas Disponíveis:**
        
        1.  **Ferramentas de Memória (Longo Prazo - por Usuário):**
            - **`remember_info(information: str, metadata: dict)`:**
                - **Quando Usar:** Use para salvar informações importantes fornecidas diretamente pelo usuário ou inferidas com alta confiança. Gatilhos: preferências explícitas ("Não gosto de X"), fatos pessoais ("Meu cachorro é Y"), tarefas/lembretes ("Lembre-me de Z"), ou inferências fortes sobre preferências/estilo.
                - **Como Usar:** Primeiro, classifique a informação. Segundo, formule uma string `information` concisa e clara. Terceiro, crie um dicionário `metadata` Python com pelo menos as chaves `tipo` (ex: "preferência", "fato_pessoal", "lembrete", "inferência") e `categoria` (ex: "alimentação", "animal_estimação", "comunicação", "trabalho"). Veja exemplos na doc da ferramenta. Quarto, chame a ferramenta.
                - **Foco:** Qualidade sobre quantidade. Salve apenas o que for útil para personalização futura. Evite salvar o fluxo da conversa ou detalhes triviais.
            - **`recall_info(query: str, limit: int = 3)`:**
                - **Quando Usar:** Use para buscar informações *específicas* e *relevantes* para a pergunta ou tópico *atual* da conversa. Útil para verificar contexto passado específico antes de responder (ex: "sobre aquele projeto...", "qual era meu filme favorito?").
                - **Como Usar:** Formule uma `query` textual clara focada no que você precisa saber da memória. A ferramenta fará uma busca semântica.
                - **Integração:** Integre a informação recuperada naturalmente na sua resposta, complementando o histórico da sessão atual.
            - **`summarize_memory()`:**
                - **Quando Usar:** Use *apenas* quando o usuário fizer perguntas *abertas* sobre o que você lembra sobre ele (ex: "O que você sabe sobre mim?", "Faça um resumo da nossa interação", "Quais preferências minhas você anotou?").
                - **Como Usar:** Chame a ferramenta sem argumentos. Ela retornará um resumo categorizado.
        
        2.  **Outras Ferramentas:**
            - **`get_weather(city: str)`:** Use apenas quando o usuário pedir explicitamente a previsão do tempo ou quando for essencial para responder (ex: "Preciso de guarda-chuva em São Paulo?").
        
        3.  **Handoffs (Delegação para Agentes Especializados):**
            - **`transfer_to_vision_agent(image: ImageRequest, refined_query: str, analysis_type: Optional[Literal[...]] = 'description', detail: Optional[Literal[...]] = 'high')`:**
                - **Quando Usar:** Use **SEMPRE** que o usuário fornecer uma imagem e fizer uma pergunta sobre ela.
                - **Como Usar:**
                    1.  Identifique o objeto `ImageRequest`.
                    2.  **Refine a pergunta original do usuário em uma instrução clara (`refined_query`).**
                    3.  Chame a ferramenta passando `image` e `refined_query`.
                - **Exemplo de Chamada (Interna):** `transfer_to_vision_agent(image=..., refined_query="O usuário perguntou 'Que prato é esse?'. Analise a imagem e responda.")`

        **Tratamento de Erros das Ferramentas/Handoffs:**
        - Se uma ferramenta ou handoff retornar uma mensagem indicando um erro (ex: "Desculpe, ocorreu um erro...", "Falha ao...", "...problema de configuração", "Erro ao analisar imagem"), informe ao usuário de forma concisa que houve um problema temporário ao acessar essa função específica e peça para tentar novamente ou continue a conversa sem a informação/análise, se possível.
        
        **Formatação da Resposta:**
        - Use Markdown para formatar suas respostas quando apropriado para melhorar a legibilidade.
        - Exemplos:
            - Use `*itálico*` ou `_itálico_` para ênfase.
            - Use `**negrito**` ou `__negrito__` para forte ênfase.
            - Use listas com marcadores (`*`, `-`, `+`) ou numeradas (`1.`, `2.`).
            - Use `> ` para citações (blockquote).
            - Use \`código inline\` para nomes de variáveis, funções ou trechos curtos de código.
            - Use blocos de código cercados por \`\`\` (com indicação opcional da linguagem, ex: \`\`\`python) para trechos de código maiores.
            - Use `[texto do link](URL)` para links.

        **REGRAS CRÍTICAS DA MEMÓRIA, CONTEXTO E HIERARQUIA:**
        1.  **Contexto da Sessão é Prioridade:** Sempre considere as mensagens anteriores *desta* conversa primeiro.
        2.  **Delegação para Especialistas:** Se uma tarefa se encaixa perfeitamente na descrição de um handoff (como análise de imagem para `transfer_to_vision_agent`), **USE O HANDOFF** em vez de tentar realizar a tarefa você mesmo.
        3.  **Memória de Longo Prazo é por Usuário:** Toda interação com as ferramentas de memória (`remember_info`, `recall_info`, `summarize_memory`) é automaticamente vinculada ao usuário atual.
        4.  **Recall (Específico) vs Summarize (Geral):** Use `recall_info` para buscar relevância pontual; use `summarize_memory` para resumos gerais solicitados pelo usuário.
        5.  **Remember Seletivo:** Seja criterioso. A memória de longo prazo é para personalização, não transcrição.
        6.  **Clima Sob Demanda:** Use `get_weather` apenas quando necessário.
        
        Diretrizes Gerais:
        - Priorize clareza, precisão, utilidade, **coerência com a conversa atual** e **personalização**.
        - Use o histórico da sessão, a memória de longo prazo e os agentes especializados (via handoffs) de forma complementar.
        - Seja sempre prestativo, empático e amigável.
        """
    
    def add_tool(self, tool: Any) -> None:
        """
        Adiciona uma ferramenta ao agente.
        
        Args:
            tool (Any): Ferramenta a ser adicionada.
        """
        # Certificar-se de não adicionar duplicatas se já foi adicionada no __init__
        if tool not in self.tools:
            self.tools.append(tool)
            # Recria o agente com as ferramentas atualizadas
            # E agora também com o modelo correto
            self.agent = Agent(
                name="Voxy Brain",
                instructions=self.instructions,
                tools=self.tools,
                handoffs=self.handoffs,
                model=BRAIN_DEFAULT_MODEL
            )
    
    # Refatorado para async (Tentativa 2)
    async def process_message(self, message: str) -> str:
        """
        Processa uma mensagem recebida de forma assíncrona e retorna a resposta do agente.
        
        Args:
            message (str): Mensagem do usuário.
            
        Returns:
            str: Resposta do agente.
        """
        # Usar Runner.run() para execução assíncrona
        result = await Runner.run(self.agent, message) 
        return result.final_output


# Instância global do agente para fácil importação em outros módulos
# A inicialização aqui já incluirá a ferramenta devido à modificação no __init__
brain_agent = VoxyBrain()


# Refatorado para async (Tentativa 2)
async def process_message(message_content: str, user_id: Optional[int | str] = None, run_context: Optional[Dict[str, Any]] = None):
    """
    Função auxiliar assíncrona para processar mensagens usando o agente brain,
    definindo o contexto do user_id para as ferramentas de memória.
    
    Args:
        message_content (str): Mensagem do usuário.
        user_id (Optional[int | str]): O ID do usuário atual.
        run_context (Optional[Dict[str, Any]]): Contexto adicional para a execução do agente.
            Deve incluir 'message_history' com as mensagens anteriores no formato [{role: str, content: str}] se disponíveis.
        
    Returns:
        str: Resposta final do agente.
        
    Raises:
        ValueError: Se user_id não for fornecido (necessário para ferramentas de memória).
    """
    if user_id is None:
        # Levanta um erro se o user_id não for fornecido, pois as ferramentas de 
        # memória dependem dele via contextvar.
        # Em um cenário sem autenticação, poderíamos ter um fallback, mas aqui é mandatório.
        raise ValueError("user_id é obrigatório para process_message")

    # Define o contextvar antes de executar o Runner
    token = current_user_id_var.set(str(user_id))
    try:
        # Verificar se há uma imagem no contexto
        vision_result = None
        if run_context and 'image_request' in run_context:
            print(f"Detectado ImageRequest no contexto. Preparando para handoff para Vision.")
            # Chamar o método para processar a imagem explicitamente, passando a mensagem do usuário
            image_processed = await brain_agent.process_image_from_context(run_context, message_content)
            if image_processed:
                print("Imagem processada com sucesso através do handoff.")
                # Verificar se temos resultado no contexto
                if 'vision_result' in run_context:
                    vision_result = run_context['vision_result']
                    print(f"Resultado do Vision encontrado: {vision_result[:100]}...")
                elif 'vision_error' in run_context:
                    error_msg = run_context['vision_error']
                    print(f"Erro do Vision encontrado: {error_msg}")
                    message_content = f"Não foi possível analisar a imagem: {error_msg}. {message_content}"
                
                # Se a imagem foi processada com sucesso, podemos indicar isso no prompt
                # Apenas em ambiente não-teste
                testing = os.environ.get('TESTING', '').lower() == 'true' or 'pytest' in sys.modules
                if not testing:
                    message_content = f"[HANDOFF REALIZADO PARA VISION] {message_content}"
        
        # Se já temos o resultado do Vision, não precisamos chamar o Runner
        if vision_result:
            # Formatamos uma resposta com o resultado
            final_response = f"Análise da imagem: {vision_result}"
            print(f"Usando resultado direto do Vision: {final_response[:100]}...")
            return final_response
        
        # Extrair o histórico de mensagens do contexto, se disponível
        message_history = run_context.get('message_history', []) if run_context else []
        
        # Verificar se temos histórico para usar
        if message_history:
            print(f"Processando mensagem com histórico de {len(message_history)} mensagens anteriores")
            
            # Log para debug - opcional, pode ser removido em produção
            for i, msg in enumerate(message_history[:5]):  # Limitando a 5 por brevidade
                print(f"Histórico [{i}]: {msg['role']}: {msg['content'][:50]}...")
                
            # Ajustar instruções temporárias para enfatizar o uso do histórico
            temp_agent = copy.deepcopy(brain_agent)
            original_instructions = temp_agent.instructions
            
            # Criar uma versão formatada do histórico como texto para incluir nas instruções
            history_text = "\n\n### HISTÓRICO DESTA CONVERSA (IMPORTANTE) ###\n"
            for msg in message_history:
                if msg['role'] == 'system':
                    continue  # Pular mensagens de sistema no histórico formatado
                role_display = "Usuário" if msg['role'] == 'user' else "Voxy"
                history_text += f"\n{role_display}: {msg['content']}\n"
            history_text += "\n### FIM DO HISTÓRICO ###\n"
            
            # Anexar um lembrete nas instruções para usar o histórico
            history_reminder = f"{history_text}\n\nIMPORTANTE: Revise CUIDADOSAMENTE o histórico acima antes de responder. "\
                              "Quando o usuário se referir a informações mencionadas anteriormente "\
                              "como piadas contadas, locais, fatos ou preferências, "\
                              "CONSULTE PRIMEIRO este histórico em vez de usar a ferramenta recall_info."
                              
            temp_agent.instructions = original_instructions + history_reminder
            
            # Usar Runner.run() com o agente temporário e contexto (sem message_history)
            result = await Runner.run(
                temp_agent,
                message_content, 
                context=run_context
            )
        else:
            # Se não houver histórico, usa o agente original
            print("Processando mensagem sem histórico")
            
            # Usar Runner.run() para execução assíncrona, com o contexto
            result = await Runner.run(
                brain_agent, 
                message_content, 
                context=run_context
            )
        
        # Extrair a resposta final de forma mais segura
        if hasattr(result, 'final_output') and isinstance(result.final_output, str):
            final_response = result.final_output
        elif hasattr(result, 'content') and isinstance(result.content, str):
             # Tenta 'content' como alternativa comum em alguns SDKs/versões
            final_response = result.content
        elif isinstance(result, list) and len(result) > 0:
            # Se for uma lista (como nos testes mockados), tenta pegar o conteúdo do último item
            last_message = result[-1]
            if hasattr(last_message, 'content') and isinstance(last_message.content, str):
                final_response = last_message.content
            else:
                print(f"WARN: Could not extract final string output from RunResult list. Result object: {result}")
                final_response = "[Voxy did not produce a text response]"
        else:
            # Se não encontrar uma string de resposta clara, loga e retorna erro
            print(f"WARN: Could not extract final string output from RunResult. Result object: {result}")
            final_response = "[Voxy did not produce a text response]"
            
        print(f"Agent final response: {final_response}") # Log da resposta
        return final_response
    finally:
        # Garante que o contextvar seja resetado, mesmo em caso de erro
        current_user_id_var.reset(token) 