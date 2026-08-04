# Arquitetura Geral da RDL

A **xApp RDL** é construída em **Python** utilizando a biblioteca oficial `ricxappframe`, que abstrai as complexidades de comunicação do RIC.

## Visão Macro

A xApp atua como um "Homem no Meio" (Man-in-the-middle) inteligente.
1. **Ouvir a Rede:** Ela assina as métricas da estação rádio-base (srsRAN gNB) usando o protocolo **E2SM-KPM**.
2. **Ouvir as outras xApps:** Ela intercepta intenções de mudança feitas por outras aplicações.
3. **Pensar:** Ela processa essas informações internamente usando grafos e Inteligência Artificial.
4. **Agir:** Ela despacha o comando final e otimizado de volta para a rádio-base usando o protocolo **E2SM-RC**.

---

## O Ciclo Fechado (Closed Loop)
Um "Ciclo Fechado" significa que o sistema observa, decide e atua de forma contínua, sem intervenção humana. Na RDL, esse fluxo funciona da seguinte maneira:

1. **RIC_INDICATION (Coleta):**
   - Mensagens da rede chegam via barramento de mensagens (RMR).
   - O payload é um dado binário altamente compactado (ASN.1 APER).
   - O `asn1_decoder.py` o transforma em dados legíveis (ex: Megabits por segundo, atraso, PRBs usados).
   - O **PerceptionAgent** atualiza o "estado da rede".

2. **RDL_ACTION_PROPOSAL (Proposta):**
   - Outra xApp (ex: QoS) envia uma proposta de ação para a RDL via RMR.
   - O **PerceptionAgent** verifica: "Essa ação conflita com o que a xApp de Energia acabou de pedir?"
   - Se houver conflito (direto ou indireto), um `ConflictEvent` é gerado.

3. **Resolução (Raciocínio):**
   - O **ReasoningAgent** assume. Ele verifica regras rígidas (Prioridade) ou aciona a IA (MAPPO) para decidir qual das xApps deve "vencer" a disputa.

4. **Validação (Refinamento):**
   - O **RefinementAgent** age como o último guarda de segurança. Ele garante que a ação decidida pela IA não está fora dos limites de segurança aceitáveis para a rede.

5. **RIC_CONTROL_REQUEST (Atuação):**
   - A decisão validada é reempacotada.
   - A RDL envia o comando final via RMR de volta para o RIC, que o roteia para a antena.

---

## Persistência e Memória (SDL e Memgraph)

O Near-RT RIC exige que xApps sejam do tipo "Stateless" (sem estado), ou seja, se a xApp reiniciar, ela não deve perder suas memórias.

- **SDL (Shared Data Layer):** É o banco de dados Redis padrão do RIC. A RDL usa o SDL para salvar seus estados básicos usando a flag do `ricxappframe`.
- **Knowledge Graph (Memgraph):** Para armazenar relacionamentos complexos de conflitos (ex: "A Ação X da xApp Y sempre afeta negativamente o KPI Z"), nós criamos o `MemoryModule`. Ele utiliza **Memgraph** (um banco de dados focado em grafos, rápido e compatível com C/C++) e **NetworkX** para buscas rápidas em memória.

## Métricas e Observabilidade

Como sabemos se a xApp está indo bem?
Usamos o **Prometheus**. A classe `metrics_server.py` sobe um pequeno servidor HTTP na porta `8081`. 
Lá, painéis como o Grafana podem ler informações como:
- Quantos conflitos foram detectados.
- Quanto tempo (latência) a IA levou para decidir.
- Quantas ações foram negadas por violarem as regras de segurança.
