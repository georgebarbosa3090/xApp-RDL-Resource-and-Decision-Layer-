# Análise de Progresso da xApp-RDL

Fiz uma análise detalhada da estrutura atual do repositório em comparação com o **Cronograma Discricionário de Execução da xApp-RDL (2026–2027)**.

## 📊 Status Atual vs. Cronograma

A abordagem atual do repositório tem sido **horizontal** (criação de esqueletos e módulos para quase todas as fases futuras) em vez de seguir a validação estrita, fase a fase, proposta pelo cronograma.

### Fase 0 — Organização científica e engenharia (Ago 17 - Ago 31, 2026)
| Entrega | Status | Observações |
| :--- | :---: | :--- |
| `research_problem.md` | ❌ Falta | Problema científico não formalizado no repositório. |
| `hypotheses.md` | ❌ Falta | Hipóteses (H1 a H4) não documentadas. |
| Arquitetura v1 | ✅ Entregue | Presente em `docs/01_arquitetura.md` e `arquitetura.png`. |
| ADRs (`docs/adr/`) | ❌ Falta | Histórico de decisões arquiteturais ausente. |
| CI (GitHub Actions) | ❌ Falta | Pipeline de lint e testes automatizados ausente (`.github/workflows`). |
| Ambientes (Docker/K8s) | ⚠️ Parcial | `docker/` e `deploy/kubernetes/` criados, mas carecem de testagem completa E2E. |
| Reprodutibilidade | ❌ Falta | Diretório `configs/experiments/` para seeds e configurações ausente. |

### Fase 1 — Estabilização da arquitetura e código (Ago - Set 2026)
| Entrega | Status | Observações |
| :--- | :---: | :--- |
| Entidades de Domínio | ✅ Entregue | `src/domain/` possui as definições base. |
| Testabilidade | ✅ Entregue | Estrutura `tests/` e `pytest.ini` criadas. |
| API Contract | ❌ Falta | Contrato formal (OpenAPI/gRPC) das integrações ausente. |
| README | ✅ Entregue | Bem estruturado e detalhado. |

### Fase 2 e 3 — Perception & Conflict Detection (Set - Out 2026)
| Entrega | Status | Observações |
| :--- | :---: | :--- |
| Parsing e KPM (ASN.1) | ✅ Entregue | Implementado em `src/e2/` (`e2ap_decoder.py`, `kpm_decoder.py`). |
| Cache Redis (SDL) | ✅ Entregue | Implementado via `infrastructure/sdl_repository.py`. |
| Classes de Conflito | ⚠️ Parcial | `conflict_types.py` e `conflicts.py` criados, mas a verificação completa (Direto, Indireto, Temporal e Política) precisa de validação de cobertura. |

### Fases Futuras (4 a 8) - Implementadas antecipadamente
Nota-se que componentes de fases futuras já possuem código no repositório:
- **MAPPO (Fase 6)**: `src/agents/marl/mappo_agent.py`
- **Memory (Fase 5)**: `src/memory_module.py`
- **Refinement (Fase 7)**: `src/refinement_agent.py`
- ❌ **Knowledge Graph (Fase 4)**: Único componente principal que não possui estrutura iniciada no código.

## 📚 Análise dos Novos Documentos e Diferenciais da Proposta

A revisão dos documentos complementares permite um posicionamento muito claro da **xApp-RDL** em relação ao estado da arte e às infraestruturas de pesquisa mais recentes.

### 1. Monitoramento Adaptativo de Métricas (Dissertação de Matheus Dória, 2025)
- **Como agrega:** A dissertação prova que a coleta contínua de KPIs na interface E2 consome muita CPU e energia do RIC. A xApp-RDL precisa de uma *Perception Layer* eficiente. Integrar a lógica de "amostragem adaptativa baseada em risco" (fases KEP/SDP) do trabalho de Dória à *Perception Layer* da xApp-RDL otimizará drasticamente a ingestão de dados.
- **O Diferencial da xApp-RDL:** O trabalho de Dória foca exclusivamente em otimizar a **coleta (leitura)** para economizar recursos. A xApp-RDL atua na **resolução de conflitos de controle (escrita/atuação)** de múltiplas xApps. Enquanto Dória propõe um monitoramento inteligente, a xApp-RDL propõe uma orquestração cognitiva (usando MARL e Knowledge Graph) para decidir *como* e *quando* atuar na RAN de forma cooperativa.

### 2. NORI: Simulação NS-3 integrada ao Near-RT RIC (Artigo Andrey et al.)
- **Como agrega:** O NORI fornece o *testbed* ideal e a infraestrutura de experimentação (E2SM-KPM, 5G-LENA) que a xApp-RDL utilizará (Fases 8 a 12) para validação. Ele garante que os experimentos propostos (como QoS vs Energy) possam ser executados em um ambiente de *closed-loop* realista.
- **O Diferencial da xApp-RDL:** O NORI é a **plataforma de infraestrutura** (o ambiente de simulação/interface). A xApp-RDL é a **camada de inteligência/cérebro** (Resource and Decision Layer) que roda *sobre* o RIC conectado ao NORI. O NORI viabiliza a pesquisa, e a xApp-RDL entrega a inovação cognitiva.

### 3. Espinha Dorsal Cognitiva MAPPO
- **Como agrega:** O documento consolida a matemática e a lógica (Estado, Recompensa, Actor/Critic) por trás do motor de raciocínio da xApp-RDL. Ele define perfeitamente como conflitos *indiretos* (ex: reduzir potência por economia vs. aumentar time-to-trigger por mobilidade gerando degradação de SLA) serão traduzidos para a IA.
- **O Diferencial da xApp-RDL:** Transforma o conceito abstrato de "resolução de conflitos" em um pipeline mensurável via MAPPO com CTDE (Centralized Training, Decentralized Execution), preenchendo as lacunas deixadas por frameworks baseados em regras (CMF) ou Teoria dos Jogos.

---

## 🎯 Melhorias a serem Formalizadas

Para alinhar o desenvolvimento com as diretrizes do projeto de pesquisa, recomendo formalizarmos as seguintes ações (que podem ser atacadas imediatamente):

> [!IMPORTANT]
> **1. Fechar o Escopo da Fase 0 Científica**
> O rigor científico é vital para a dissertação/artigos. Precisamos criar:
> - `docs/research_problem.md`
> - `docs/hypotheses.md` (Formalizando H1 a H4)
> - `docs/adr/` (Para registrar por que MAPPO foi escolhido, por que Redis vs InfluxDB, etc.)

> [!TIP]
> **2. Implementar Pipeline de CI/CD (GitHub Actions)**
> Criar o diretório `.github/workflows/ci.yml` para garantir que o código passe pelos testes (`pytest`) automaticamente a cada commit, evitando degradação conforme o MAPPO e o Knowledge Graph forem sendo integrados.

> [!WARNING]
> **3. Arquitetura de Experimentos (Reprodutibilidade)**
> A Fase 0 exige a criação do diretório `configs/experiments/`. Precisamos padronizar como os experimentos serão executados (seeds, cenários) para facilitar as Fases 9 a 13 (Ablation Study e Baselines).

> [!NOTE]
> **4. Design de Contratos (API Contract)**
> Formalizar a comunicação (via OpenAPI/Swagger ou Protobuf/gRPC) para a ingestão de propostas externas, tornando a arquitetura efetivamente desacoplada.

> [!TIP]
> **5. Integração de Monitoramento Adaptativo na Perception Layer**
> Atualizar o código da `Perception Layer` (ex: `src/perception_agent.py`) para incorporar a amostragem adaptativa baseada em risco proposta por Matheus Dória. Isso reduzirá o *overhead* do próprio testbed NORI durante as fases experimentais.

Como deseja prosseguir? Podemos começar criando os **arquivos científicos da Fase 0 (Hypotheses, Problem)** ou focar na **infraestrutura de CI/CD (GitHub Actions)** primeiro?
