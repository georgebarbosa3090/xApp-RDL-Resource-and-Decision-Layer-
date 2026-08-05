# Módulos de Inteligência Artificial

A RDL é considerada um Orquestrador Cognitivo porque vai além de regras de "se/então" (if/else). Seus agentes vivem no diretório `src/agents/`.

## 1. O Raciocínio (Decision Making): `reasoning_agent.py`
O **Reasoning Agent** implementa o protocolo rigoroso estabelecido por `DecisionStrategy`. Ele é chamado quando propostas concorrentes criam um conflito.

### Abordagem Híbrida:
A RDL usa abordagens conectáveis em cascata para responder abaixo dos limites de tempo O-RAN:
1. **Histórico (<< 10 ms):** Checa se esse embate numérico já aconteceu e foi resolvido recentemente (cache).
2. **Prioridade Estática (< 10 ms):** Define o peso da xApp (Segurança > QoS > Economia).
3. **Multi-Agent Reinforcement Learning (MARL) (< 100 ms):** Se for um Conflito Indireto, ele aciona a IA em `agents/marl/mappo_agent.py`.

### A Magia do MARL (`agents/marl/`)
Construída sob a engine do PyTorch e Ray, a arquitetura **MAPPO** mapeia os KPMs em observações e recompensa os atores pelas ações menos destrutivas e mais otimizadas antes de chancelar o resultado.

## 2. A Segurança e Refinamento: `refinement_agent.py`
O **Safety Guard** é o cão de guarda da antena rádio-base.
Antes do `ControlDispatcher` mandar a mensagem, a validação é executada contra as travas estritas (lidas do JSON de configuração):
- **Limite Frequencial:** Garante o `minimum_control_interval_ms` entre comandos iguais na mesma célula, abortando oscilações espasmódicas (ex: ficar subindo e descendo PRB a cada 100ms).
- **Escopo e Limites:** Corta pedidos absurdos de PRB menores que zero ou maiores que 100, bem como potência (TX_POWER) fora do *baseline*.
- **Sem Alvos Vazios:** Rejeita requisições para `ue_ids` ou `cell_ids` desconhecidos (exigência `reject_unknown_targets`).
