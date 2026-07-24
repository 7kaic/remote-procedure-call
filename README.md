# remote-procedure-call

Este projeto implementa um servidor de RPC capaz de gerenciar múltiplos clientes e executar procedimentos remotos previamente definidos.

A comunicação foi projetada para ser simples e leve, utilizando exclusivamente recursos da biblioteca padrão do `Python 3.13.12`, sem qualquer dependência externa.

## Contexto

Uma chamada de procedimento remoto é uma tecnologia de comunicação entre processos que permite um programa invocar funções em outro espaço de endereçamento. Esse modelo é amplamente utilizado em soluções de gerenciamento remoto, como plataformas de RMM, sistemas de suporte técnico e ferramentas de ativos de TI.

## Funcionamento

O cliente estabalece conexão com o servidor e realiza uma identificação por meio do protocolo JSON-RPC. Uma vez identificado, entra em um ciclo contínuo de envio de beacons periódicos, consultando o servidor em busca de novas tarefas.

Quando um procedimento remoto é acionado o servidor o envia ao cliente por meio do terminal. A execução ocorre no cliente, que retorna o resultado da função de forma assíncrona via HTTP, permitindo que o servidor continue atendendo outros clientes sem bloqueio.

```
servidor                          cliente
   │                                 │
   │  ←── identify (hostname, mac) ──│  conecta e se identifica
   │  ───────── client_id ──────────→│
   │                                 │
   │  ←──────── beacon ───────────── │  polling periódico por tarefas
   │  ──────── task (ou 204) ───────→│
   │                                 │
   │  ←──────── task_result ──────── │  resultado da execução
```
---

