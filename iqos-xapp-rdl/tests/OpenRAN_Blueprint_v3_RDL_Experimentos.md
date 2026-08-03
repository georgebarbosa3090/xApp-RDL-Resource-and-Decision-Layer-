# Teste do xApp-RDL combinado com outra xApp no OpenRAN@Brasil Blueprint v3

## Tutorial de ambiente experimental para o xApp-RDL

## 1. Objetivo e escopo

Este documento descreve um ambiente reproduzível para desenvolver, implantar e avaliar o **xApp-RDL (Resource and Decision Layer)** em uma máquina virtualizada. O protocolo cobre:

- OSC Near-RT RIC;
- xApp-RDL;
- srsRAN Project como E2 Node;
- Open5GS como 5G Core;
- srsUE com ZeroMQ para execução sem rádio físico;
- E2SM-KPM para coleta de medições;
- E2SM-RC para ações de controle;
- captura de tráfego E2;
- curvas de treinamento MAPPO;
- medição da latência do ciclo fechado;
- comprovação de atuação sobre parâmetros reais suportados pela RAN;
- alternativa de validação em OpenRAN@Brasil Blueprint/NORI.

> **Importante:** o repositório do xApp-RDL descreve uma arquitetura e um plano de implementação, mas não apresenta, por si só, resultados experimentais completos. Portanto, as tabelas e procedimentos abaixo são um **protocolo de execução e avaliação**. Resultados somente devem ser preenchidos após medições reais.

---

## 2. Arquitetura experimental

```text
srsUE ──ZMQ── srsRAN gNB ──N2/N3── Open5GS
                       │
                       │ E2AP/SCTP
                       ▼
                 OSC Near-RT RIC
                       │
                       ├── E2Term / E2Mgr / SubMgr / RMR
                       │
                       └── xApp-RDL
                           ├── KPI Collector
                           ├── Perception Agent
                           ├── Reasoning Agent
                           ├── Refinement Agent
                           ├── Action Arbiter
                           ├── E2 Control Encoder
                           ├── Memory / SDL
                           └── Metrics / Logs
```

A figura PNG que acompanha este documento apresenta essa arquitetura sem comentários laterais.

---

## 3. Requisitos da máquina virtual

### 3.1 Configuração mínima funcional

| Recurso | Mínimo |
|---|---:|
| vCPU | 8 |
| RAM | 16 GB |
| Disco | 120 GB SSD |
| Interfaces de rede | 1 NAT + 1 host-only ou bridge |
| Sistema operacional | Ubuntu 22.04 LTS |
| Virtualização | KVM/QEMU, VMware Workstation/ESXi ou VirtualBox |

### 3.2 Configuração recomendada para treinamento e experimentos

| Recurso | Recomendado |
|---|---:|
| vCPU | 16 |
| RAM | 32 GB |
| Disco | 250–500 GB SSD |
| GPU | opcional; NVIDIA com 8 GB ou mais |
| Interfaces de rede | 2 |
| Reserva de CPU | habilitar CPU pinning quando disponível |
| Sincronização de tempo | chrony |
| Snapshot | antes de cada grande etapa |

Para uma instalação completa do OSC Near-RT RIC em Kubernetes, prefira 16 vCPU e 32 GB. Para um primeiro teste de interoperabilidade, a implantação mínima em Docker Compose mantida pelo srsRAN reduz a complexidade.

---

## 4. Topologias recomendadas

### 4.1 Topologia A — uma única VM

Adequada para aprendizagem e teste inicial:

```text
VM-01
├── Open5GS
├── OSC Near-RT RIC
├── srsRAN gNB
├── srsUE
├── xApp-RDL
├── Prometheus
└── Grafana
```

Vantagens:

- configuração simples;
- menor dependência de rede;
- ideal para validar E2 Setup, subscription e KPM.

Limitações:

- interferência entre componentes;
- latência contaminada pelo compartilhamento de CPU;
- menos adequada para resultados finais.

### 4.2 Topologia B — três VMs

Recomendada para a dissertação:

```text
VM-RIC
├── OSC Near-RT RIC
├── xApp-RDL
├── Prometheus
└── Grafana

VM-RAN
├── srsRAN gNB
└── srsUE / ZMQ

VM-CORE
└── Open5GS
```

Endereçamento sugerido:

| Máquina | Interface experimental |
|---|---|
| VM-RIC | 192.168.56.10 |
| VM-RAN | 192.168.56.20 |
| VM-CORE | 192.168.56.30 |

Portas relevantes:

| Serviço | Porta/protocolo |
|---|---|
| E2 | 36421/SCTP |
| NGAP | 38412/SCTP |
| GTP-U | 2152/UDP |
| Prometheus | 9090/TCP |
| Grafana | 3000/TCP |
| xApp metrics | 8080/TCP |

---

## 5. Preparação do Ubuntu

```bash
sudo apt update
sudo apt full-upgrade -y

sudo apt install -y \
  git curl wget jq unzip zip \
  build-essential cmake ninja-build pkg-config \
  python3 python3-pip python3-venv \
  libsctp-dev lksctp-tools \
  libfftw3-dev libmbedtls-dev libyaml-cpp-dev \
  libgtest-dev libboost-program-options-dev \
  libzmq3-dev tcpdump tshark wireshark \
  chrony net-tools iproute2
```

Desabilite swap quando usar Kubernetes:

```bash
sudo swapoff -a
sudo sed -i.bak '/\sswap\s/s/^/#/' /etc/fstab
```

Carregue módulos e parâmetros de rede:

```bash
cat <<'EOF' | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter

cat <<'EOF' | sudo tee /etc/sysctl.d/99-kubernetes.conf
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
EOF

sudo sysctl --system
```

Verifique SCTP:

```bash
lsmod | grep sctp || sudo modprobe sctp
```

---

## 6. Instalação do Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

sudo usermod -aG docker "$USER"
newgrp docker

docker --version
docker compose version
```

Configure rotação de logs:

```bash
cat <<'EOF' | sudo tee /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "5"
  }
}
EOF

sudo systemctl restart docker
```

---

## 7. Caminho recomendado 1: OSC Near-RT RIC mínimo para interoperabilidade

O srsRAN mantém um ambiente reduzido do OSC Near-RT RIC para testes.

```bash
cd "$HOME"
git clone https://github.com/srsran/oran-sc-ric.git
cd oran-sc-ric
docker compose up -d
docker compose ps
docker compose logs -f
```

Critério de sucesso:

```text
ric_submgr | RMR is ready now ...
```

Verifique a porta E2:

```bash
sudo ss -lpn | grep 36421
```

Esse caminho é recomendado para:

- validar conexão E2;
- receber KPMs;
- capturar PCAP;
- executar a primeira versão do xApp;
- depurar sem Kubernetes.

---

## 8. Caminho recomendado 2: OSC Near-RT RIC completo em Kubernetes

Use esse caminho quando o xApp estiver funcional e for necessário avaliar:

- AppMgr;
- RtMgr;
- SDL/DBaaS;
- namespaces;
- deployment via descriptor;
- comportamento próximo do OpenRAN@Brasil Blueprint.

### 8.1 Instalação por scripts oficiais

```bash
cd "$HOME"
git clone https://gerrit.o-ran-sc.org/r/ric-plt/ric-dep
cd ric-dep/bin

sudo ./install_k8s_and_helm.sh
./install_common_templates_to_helm.sh
```

Edite a recipe estável:

```bash
cd "$HOME/ric-dep"
cp RECIPE_EXAMPLE/PLATFORM/example_recipe_latest_stable.yaml \
   RECIPE_EXAMPLE/PLATFORM/rdl_recipe.yaml
nano RECIPE_EXAMPLE/PLATFORM/rdl_recipe.yaml
```

Instale:

```bash
cd "$HOME/ric-dep/bin"
./install -f ../RECIPE_EXAMPLE/PLATFORM/rdl_recipe.yaml
```

Verifique:

```bash
kubectl get nodes -o wide
kubectl get pods -A
kubectl get svc -A
helm list -A
```

Todos os pods necessários devem estar `Running` ou `Completed`.

### 8.2 Namespaces esperados

```text
ricinfra
ricplt
ricxapp
```

---

## 9. Alternativa OpenRAN@Brasil Blueprint/NORI

O repositório OpenRAN@Brasil Blueprint fornece imagens de VM já preparadas para desenvolvimento e teste de xApps no OSC Near-RT RIC. O NORI amplia esse ambiente com integração ao ns-3.

Use dois estágios:

1. **srsRAN real/emulado:** validar interoperabilidade E2, KPM e controle suportado;
2. **NORI/ns-3:** escalar número de células, UEs e episódios de treinamento.

Procedimento geral:

```bash
git clone https://github.com/LABORA-INF-UFG/openran-br-blueprint.git
cd openran-br-blueprint
```

Siga o guia da versão de Blueprint compatível com o laboratório. Registre no relatório:

- nome da imagem;
- checksum;
- versão do Blueprint;
- commit do repositório;
- versão do ns-3;
- versão do NORI;
- versão do OSC RIC.

---

## 10. Instalação do srsRAN Project

```bash
cd "$HOME"
git clone https://github.com/srsran/srsRAN_Project.git
cd srsRAN_Project

mkdir -p build
cd build

cmake ../ \
  -DENABLE_EXPORT=ON \
  -DENABLE_ZEROMQ=ON \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo

make -j"$(nproc)"
sudo make install
sudo ldconfig
```

Confirme que o CMake encontrou ZeroMQ.

Registre a versão:

```bash
git rev-parse HEAD
git describe --tags --always
```

---

## 11. Open5GS

Para a primeira execução, use o 5GC dockerizado fornecido pelo srsRAN:

```bash
cd "$HOME/srsRAN_Project/docker"
docker compose up -d 5gc
docker compose ps
```

Teste:

```bash
docker compose logs -f 5gc
```

---

## 12. Configuração E2 do gNB

No arquivo YAML do gNB:

```yaml
e2:
  enable_du_e2: true
  e2sm_kpm_enabled: true
  e2sm_rc_enabled: true
  addr: 192.168.56.10
  port: 36421
```

Para uma única VM, use `127.0.0.1` quando o RIC expuser a porta localmente.

Ative PCAP:

```yaml
pcap:
  e2ap_enable: true
  e2ap_du_filename: /tmp/gnb_du_e2ap.pcap
  e2ap_cu_cp_filename: /tmp/gnb_cu_cp_e2ap.pcap
  e2ap_cu_up_filename: /tmp/gnb_cu_up_e2ap.pcap
```

Ative métricas necessárias ao E2SM-KPM:

```yaml
metrics:
  layers:
    enable_rlc: true
    enable_sched: true
  periodicity:
    du_report_period: 1000
```

Observação: a documentação atual do srsRAN informa período KPM limitado a 1 segundo e suporte a E2SM-RC Control Service Style 2. Não assuma que qualquer parâmetro de slicing pode ser controlado sem confirmar o RAN Function Definition anunciado pelo gNB.

---

## 13. Ordem correta de execução

```text
1. Open5GS
2. Near-RT RIC
3. srsRAN gNB
4. srsUE
5. tráfego IP
6. xApp-RDL
```

Exemplo:

```bash
# Terminal 1
cd "$HOME/srsRAN_Project/docker"
docker compose up 5gc

# Terminal 2
cd "$HOME/oran-sc-ric"
docker compose up

# Terminal 3
cd "$HOME/srsRAN_Project/build/apps/gnb"
sudo ./gnb -c /caminho/gnb_zmq.yaml \
  e2 --addr="192.168.56.10" --bind_addr="192.168.56.20"
```

---

## 14. Preparação do xApp-RDL

```bash
cd "$HOME"
git clone \
  https://github.com/georgebarbosa3090/xApp-RDL-Resource-and-Decision-Layer-.git

cd xApp-RDL-Resource-and-Decision-Layer-
git rev-parse HEAD
```

Crie ambiente Python:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
```

Execute testes:

```bash
pytest tests/ -v \
  --cov=src \
  --cov-report=term-missing \
  --cov-report=html
```

Meta inicial:

```text
cobertura ≥ 80%
```

---

## 15. Empacotamento do xApp

```bash
docker build \
  -f docker/Dockerfile \
  -t xapp-rdl:0.1.0 .
```

Teste local:

```bash
docker compose \
  -f docker/docker-compose.yml \
  up --build
```

Para o OSC completo, o descriptor deve registrar:

- nome e versão;
- imagem Docker;
- portas HTTP e RMR;
- tipos de mensagens RMR;
- políticas A1 consumidas;
- controles configuráveis.

Fluxo:

```text
Docker image
→ xApp descriptor/schema
→ dms_cli onboard
→ chart
→ install em ricxapp
```

Exemplo conceitual:

```bash
dms_cli onboard \
  CONFIG_FILE_PATH \
  SCHEMA_FILE_PATH

dms_cli install \
  XAPP_CHART_NAME \
  VERSION \
  ricxapp
```

Os parâmetros exatos dependem da versão de `dms_cli`.

---

## 16. Verificação do E2 Setup

No gNB:

```bash
sudo tcpdump -i any -nn -s 0 \
  'sctp port 36421' \
  -w results/e2_sctp_full.pcap
```

No RIC:

```bash
docker compose logs -f | grep -Ei 'E2|setup|node|subscription'
```

No Kubernetes:

```bash
kubectl logs -n ricplt \
  -l app=ricplt-e2term \
  --tail=300 -f
```

Critérios:

- SCTP association estabelecida;
- E2 Setup Request observado;
- E2 Setup Response observado;
- E2 Node registrado;
- RAN Functions anunciadas;
- KPM e RC presentes quando suportados.

---

## 17. Captura e análise do tráfego E2

### 17.1 Captura no gNB

Use os arquivos PCAP configurados no YAML.

```bash
ls -lh /tmp/*e2ap*.pcap
cp /tmp/gnb_du_e2ap.pcap results/
```

### 17.2 Captura de rede

```bash
sudo tcpdump -i any -nn -s 0 \
  -w results/e2_network.pcap \
  'sctp port 36421'
```

### 17.3 Extração com tshark

```bash
tshark -r results/e2_network.pcap \
  -Y 'sctp' \
  -T fields \
  -e frame.time_epoch \
  -e ip.src \
  -e ip.dst \
  -e sctp.srcport \
  -e sctp.dstport \
  > results/e2_sctp.csv
```

Quando o dissector E2AP estiver disponível:

```bash
tshark -r results/e2_network.pcap \
  -Y 'e2ap' \
  -T fields \
  -e frame.number \
  -e frame.time_epoch \
  -e ip.src \
  -e ip.dst \
  -e _ws.col.Info \
  > results/e2ap_messages.csv
```

Conte mensagens:

```bash
tshark -r results/e2_network.pcap \
  -Y 'e2ap' \
  -T fields -e _ws.col.Info |
sort | uniq -c
```

Comprovação mínima:

- E2 Setup;
- RIC Subscription Request;
- RIC Subscription Response;
- RIC Indication;
- RIC Control Request, quando houver;
- RIC Control Acknowledge ou Failure.

---

## 18. Instrumentação da latência

A latência científica deve ser separada em componentes.

### 18.1 Definições

```text
t0 = chegada da RIC Indication à xApp
t1 = conclusão da percepção
t2 = conclusão do raciocínio
t3 = conclusão do refinamento
t4 = emissão do RIC Control Request
t5 = chegada do ACK/Failure
```

Métricas:

```text
L_perception = t1 - t0
L_reasoning  = t2 - t1
L_refinement = t3 - t2
L_xapp       = t4 - t0
L_control    = t5 - t4
L_total      = t5 - t0
```

### 18.2 Logging estruturado

Cada decisão deve produzir JSON:

```json
{
  "experiment_id": "EXP-RDL-001",
  "episode": 12,
  "step": 340,
  "conflict_id": "C-000393",
  "t_indication_ns": 0,
  "t_perception_ns": 0,
  "t_reasoning_ns": 0,
  "t_refinement_ns": 0,
  "t_control_tx_ns": 0,
  "t_control_ack_ns": 0,
  "decision_path": "static|mappo",
  "validation_level": 1,
  "action": {},
  "result": "ack|failure|timeout"
}
```

Use relógio monotônico:

```python
from time import perf_counter_ns
timestamp = perf_counter_ns()
```

### 18.3 Estatísticas obrigatórias

- média;
- desvio-padrão;
- mediana;
- p90;
- p95;
- p99;
- máximo;
- CDF;
- histograma;
- taxa de timeout.

---

## 19. Curvas de treinamento MAPPO

### 19.1 Variáveis que devem ser registradas

Por episódio:

- recompensa total;
- recompensa por agente;
- throughput;
- latência;
- violações de SLA;
- energia;
- conflitos detectados;
- conflitos resolvidos;
- entropy;
- actor loss;
- critic loss;
- KL divergence;
- explained variance;
- comprimento do episódio.

Formato CSV:

```text
experiment_id,seed,episode,reward,actor_loss,critic_loss,entropy,
throughput_mbps,latency_ms,sla_violations,energy_j,conflicts,resolved
```

### 19.2 Repetição

Use pelo menos:

```text
5 sementes para protótipo
10 sementes para artigo/dissertação
```

Exemplo:

```bash
for seed in 11 22 33 44 55; do
  python -m training.train_mappo \
    --seed "$seed" \
    --episodes 10000 \
    --output "results/train/seed_${seed}"
done
```

### 19.3 Suavização

Não publique apenas curva suavizada. Armazene e disponibilize:

- curva bruta;
- média móvel;
- média entre sementes;
- intervalo de confiança de 95%.

---

## 20. Comprovação de atuação sobre parâmetros reais

Uma afirmação de “controle real” exige quatro evidências simultâneas.

### Evidência A — comando emitido

- log da xApp;
- `ResolutionAction`;
- RIC Control Request no PCAP.

### Evidência B — confirmação de protocolo

- RIC Control Acknowledge;
- ausência de Failure;
- correlação pelo request ID.

### Evidência C — alteração interna no gNB

- log do handler E2SM-RC;
- variável ou configuração alterada;
- timestamp correspondente.

### Evidência D — efeito mensurável

- KPM antes;
- KPM depois;
- janela de controle;
- grupo de comparação.

Tabela:

| Campo | Valor |
|---|---|
| Parâmetro | preencher |
| Service Model | E2SM-RC |
| Control Style | preencher |
| Action ID | preencher |
| Valor anterior | preencher |
| Valor solicitado | preencher |
| Valor aplicado | preencher |
| ACK | sim/não |
| KPI afetado | preencher |
| Delta observado | preencher |

> Não use “PRB quota”, “potência” ou “scheduler” como ação comprovada até verificar que a versão do srsRAN anuncia e implementa esse controle específico.

---

## 21. Plano de experimentos

### EXP-00 — sanity check

Objetivo:

- validar instalação;
- conectar gNB ao RIC;
- receber KPM.

Duração:

```text
10 minutos
```

Critério:

```text
≥ 500 RIC Indications sem queda da associação SCTP
```

### EXP-01 — baseline sem coordenação

- xApps independentes ou ações sintéticas;
- sem RDL;
- medir conflitos e SLA.

### EXP-02 — prioridade estática

- RDL com fast path;
- sem MAPPO;
- comparar com EXP-01.

### EXP-03 — MAPPO sem refinamento

- ação do agente aplicada diretamente;
- ambiente isolado;
- medir desempenho e risco.

### EXP-04 — MAPPO com refinamento

- níveis 1 e 2 ativos;
- medir rejeição, latência e segurança.

### EXP-05 — carga crescente

Perfis:

```text
25%, 50%, 75%, 90% e 100%
```

### EXP-06 — conflito direto

Duas propostas atuam no mesmo parâmetro.

### EXP-07 — conflito indireto

Duas propostas atuam em parâmetros diferentes com impacto no mesmo KPI.

### EXP-08 — escalabilidade

- 1, 2, 4, 8, 16 E2 Nodes no NORI;
- medir CPU, memória, p95 e perda de mensagens.

### EXP-09 — falhas

- reiniciar xApp;
- reiniciar E2Term;
- interromper SCTP;
- inserir timeout no MAPPO.

---

## 22. Matriz de comparação

| Variante | Regras | MAPPO | Refinamento | Grafo |
|---|---:|---:|---:|---:|
| Baseline | não | não | não | não |
| Prioridade estática | sim | não | nível 1 | não |
| MAPPO puro | não | sim | não | não |
| RDL-H | sim | sim | níveis 1–2 | não |
| RDL-HKG | sim | sim | níveis 1–2 | sim |

---

## 23. Métricas finais

### Rede

- throughput;
- latência;
- jitter;
- perda;
- utilização de PRB;
- Jain fairness;
- violações de SLA;
- energia, se disponível.

### Coordenação

- conflitos detectados;
- precision;
- recall;
- F1;
- conflitos resolvidos;
- taxa de ações rejeitadas;
- oscilações;
- reconfigurações por minuto.

### Sistema

- CPU;
- RAM;
- latência p50/p95/p99;
- taxa de mensagens E2;
- timeout;
- disponibilidade.

### Aprendizado

- reward;
- convergência;
- estabilidade entre seeds;
- sample efficiency;
- actor/critic loss;
- entropy.

---

## 24. Estrutura de diretórios dos resultados

```text
experiments/
├── configs/
│   ├── exp_00.yaml
│   ├── exp_01.yaml
│   └── ...
├── raw/
│   ├── pcap/
│   ├── logs/
│   ├── prometheus/
│   └── training/
├── processed/
│   ├── latency.csv
│   ├── kpm.csv
│   ├── controls.csv
│   └── conflicts.csv
├── figures/
├── tables/
├── scripts/
├── environment/
│   ├── versions.txt
│   ├── docker_images.txt
│   ├── pip_freeze.txt
│   └── vm_spec.txt
└── README.md
```

---

## 25. Registro do ambiente

```bash
mkdir -p experiments/environment

uname -a > experiments/environment/uname.txt
lsb_release -a > experiments/environment/os.txt
lscpu > experiments/environment/cpu.txt
free -h > experiments/environment/memory.txt
lsblk > experiments/environment/disks.txt
docker version > experiments/environment/docker.txt
docker compose version > experiments/environment/docker_compose.txt
pip freeze > experiments/environment/pip_freeze.txt
docker images --digests > experiments/environment/docker_images.txt
```

Registre commits:

```bash
git -C "$HOME/srsRAN_Project" rev-parse HEAD
git -C "$HOME/oran-sc-ric" rev-parse HEAD
git -C "$HOME/xApp-RDL-Resource-and-Decision-Layer-" rev-parse HEAD
```

---

## 26. Critérios de aceitação

### Integração E2

- E2 Setup concluído;
- subscription aceita;
- indications recebidas;
- PCAP válido.

### xApp

- testes unitários aprovados;
- cobertura ≥ 80%;
- endpoint `/health`;
- endpoint `/metrics`;
- logs correlacionáveis.

### Latência

Alvos de pesquisa do projeto:

```text
fast path: p95 < 100 ms
slow path MAPPO: registrar p95 e p99
```

O valor final deve ser medido, não presumido.

### Controle

- Request e ACK capturados;
- alteração confirmada no gNB;
- KPM posterior compatível com a ação.

---

## 27. Ameaças à validade

### Interna

- competição por CPU na mesma VM;
- aquecimento de cache;
- sincronização incorreta;
- logs bloqueantes;
- mudança de versões.

### Externa

- ZeroMQ não reproduz completamente RF real;
- um único UE não representa carga de produção;
- suporte E2SM-RC limitado;
- resultados do NORI dependem do modelo de simulação.

### De construção

- reward pode não representar SLA real;
- métricas KPM disponíveis podem ser insuficientes;
- conflito indireto depende da qualidade do grafo.

### Estatística

- poucas seeds;
- episódios insuficientes;
- comparação sem intervalo de confiança;
- seleção posterior de cenários favoráveis.

---

## 28. Checklist de publicação

- [ ] commits fixados;
- [ ] VM e imagens versionadas;
- [ ] seeds registradas;
- [ ] scripts de execução;
- [ ] dados brutos preservados;
- [ ] PCAP disponibilizado;
- [ ] logs estruturados;
- [ ] curvas brutas e suavizadas;
- [ ] IC 95%;
- [ ] análise de p95/p99;
- [ ] tabela de ações E2SM-RC;
- [ ] limitações declaradas;
- [ ] licença e README de reprodução.

---

## 29. Referências técnicas

1. O-RAN Software Community. *Near-RT RIC Deployment — Installation Guides*.
2. srsRAN Project. *O-RAN NearRT-RIC and xApp*.
3. srsRAN Project. *Installation Guide*.
4. LABORA-INF-UFG. *OpenRAN@Brasil Blueprint*.
5. OpenRAN@Brasil. *Blueprint-NORI*.
6. Santos et al. *Managing O-RAN Networks: xApp Development From Zero to Hero*.
7. Repositório do xApp-RDL — George Barbosa.

---

## 30. Próxima implementação recomendada

Para reduzir risco, implemente nesta ordem:

```text
1. E2 Setup
2. KPM monitoring
3. PCAP e logs
4. conflito sintético
5. prioridade estática
6. refinamento nível 1
7. controle E2SM-RC comprovado
8. dataset
9. MAPPO offline
10. fine-tuning controlado
11. NORI multi-célula
```

Essa ordem evita iniciar pelo MARL antes de comprovar que o ciclo E2 completo funciona.
