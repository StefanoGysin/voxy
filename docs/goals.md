# Objetivos e Contexto do Produto Voxy

Este documento descreve a visão, os objetivos e o contexto do projeto Voxy.

## 1. Visão Geral

Voxy é um sistema de agentes inteligentes projetado para ser um **orquestrador central**. Ele utiliza o **OpenAI Agents SDK** para coordenar diferentes ferramentas e, potencialmente, outros agentes especializados, a fim de responder às solicitações do usuário de forma eficaz.

O sistema é composto por um backend Python/FastAPI e um frontend React/Vite, e agora inclui **autenticação de usuário** e **memória persistente por usuário** via `mem0ai`.

## 2. Propósito e Problemas Solucionados

O principal objetivo do Voxy é simplificar a interação do usuário com sistemas complexos de IA e fornecer uma experiência personalizada:

*   **Ponto Único de Interação:** O usuário conversa apenas com o Voxy, que lida com a complexidade de escolher e usar a ferramenta ou agente certo nos bastidores.
*   **Personalização:** Através da memória persistente por usuário, Voxy pode lembrar preferências e interações passadas, adaptando suas respostas e tornando a conversa mais relevante.
*   **Abstração de Complexidade:** Automatiza a delegação e coordenação de tarefas, permitindo fluxos de trabalho mais poderosos que combinam diferentes capacidades (ex: obter dados de uma API, buscar na memória, resumir).

## 3. Experiência do Usuário Desejada

*   **Interação Natural:** A comunicação com Voxy deve ser simples, através de linguagem natural em uma interface de chat.
*   **Reconhecimento e Contexto:** Voxy deve reconhecer o usuário (após login) e utilizar o histórico de memória para manter o contexto entre sessões e personalizar a interação.
*   **Inteligência na Delegação:** Voxy deve ser capaz de entender a intenção do usuário e usar a ferramenta apropriada (como `get_weather`, `remember_info`, `recall_info`) de forma proativa e contextual.
*   **Respostas Coesas:** Mesmo que a resposta final seja composta por informações de diferentes fontes (memória, ferramentas), Voxy deve apresentá-la de forma clara e unificada.

## 4. Objetivos de UX Chave

*   **Intuitivo:** Fácil de usar sem necessidade de comandos específicos.
*   **Personalizado:** Lembra do usuário e de suas preferências/interações.
*   **Eficiente:** Respostas rápidas e precisas, enriquecidas pelo contexto.
*   **Poderoso:** Capaz de lidar com tarefas complexas através da orquestração e memória.
*   **Confiável:** Respostas consistentes.
*   **Amigável:** Tom de conversa prestativo e natural. 