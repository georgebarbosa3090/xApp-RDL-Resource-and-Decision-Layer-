# Módulos de Inteligência Artificial

A RDL é considerada um Orquestrador Cognitivo porque vai além de regras de "se/então" (if/else). Ela utiliza duas vertentes de Machine Learning implementadas através dos seus Agentes.

## 1. O Raciocínio (Decision Making): `reasoning_agent.py`
O **Reasoning Agent** é chamado sempre que o Perception Agent grita: *"Temos um conflito!"*.

### Abordagem Híbrida:
A RDL usa uma abordagem em cascata para garantir que a latência (demora para responder) seja mínima:
1. **Histórico (<< 10 ms):** Tenta buscar no Knowledge Graph uma resolução igual já feita e confirmada como segura.
2. **Prioridade Estática (< 10 ms):** Se for um Conflito Direto simples, a xApp com nível de criticidade maior vence (Ex: Segurança > QoS > Economia de Energia).
3. **Multi-Agent Reinforcement Learning (MARL) (< 100 ms):** Se for um Conflito Indireto complexo sem resposta óbvia, ele invoca o `mappo_agent.py`.

### A Magia do MARL (`mappo_agent.py`)
Utilizamos a arquitetura **MAPPO** (Multi-Agent Proximal Policy Optimization).
Ao contrário de treinar uma única IA enorme, o MARL treina vários pequenos "Agentes Críticos" e "Agentes Atores".
- Em vez de adivinhar o resultado, as redes neurais (construídas usando **PyTorch**) mapeiam o estado atual (latência, perda de pacotes) e punem ou recompensam ações simuladas internamente antes de emitir a decisão final para a rádio-base.

## 2. A Segurança e Refinamento: `refinement_agent.py`
A IA às vezes pode alucinar ou tomar decisões puramente matemáticas que não fazem sentido físico para o mundo das Telecomunicações (ex: tentar definir o número de blocos de rádio para um valor negativo).

O **Refinement Agent** atua como uma **Barreira de Segurança (Guardrail)**.
- **Checagem de Ranges:** Ele possui um dicionário em Python chamado `PARAMETER_RANGES`. Se a decisão da IA mandar aplicar `-10` PRBs, ele descarta a ação instantaneamente.
- **Checagem Semântica (Validação Nível 3):** Para decisões severas, ele pode acionar um modelo secundário (`intent_classifier.py`) baseado na biblioteca **Scikit-learn** para classificar a similaridade de intenção com base em vetores pre-treinados, negando a alteração caso não seja segura.
