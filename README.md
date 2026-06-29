# remote-procedure-call
Uma chamada de procedimento remoto é uma tecnologia de comunicação entre processos que permite a um programa invocar funções em outro espaço de endereçamento. Nesse projeto, o servidor envia procedimentos ao cliente via terminal e recebe o resultado de volta de forma assíncrona.

O cliente tenta se conectar ao servidor e se identifica via protocolo JSON-RPC. Uma vez identificado, passa a enviar beacons periódicos em busca de tarefas a executar. O resultado de cada tarefa é retornado ao servidor automaticamente.

O projeto se inspira em tecnologias como RMM e sistemas de suporte ao gerenciamento de TI e ativos.

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

O servidor segura o beacon por até 60 segundos (long-polling), respondendo imediatamente quando uma tarefa estiver disponível.

---

