# xApp RDL (Resource and Decision Layer)

## 1. Visão Geral
A **xApp RDL** é um orquestrador cognitivo para o O-RAN Near-RT RIC. Sua principal função é arbitrar intenções de controle concorrentes provenientes de múltiplas xApps em uma rede, decidindo a alocação ótima de recursos utilizando Inteligência Artificial (MAPPO) ou políticas estáticas.

## 2. Contribuição
Este projeto visa resolver o problema crítico de **Conflitos de Ação** no O-RAN, onde xApps independentes podem tentar modificar os mesmos parâmetros de rádio de forma divergente (ex: QoS vs. Energy Savings). A contribuição científica central é a delegação da ação final para a RDL.

## 3. Arquitetura
A arquitetura foi inteiramente desenhada utilizando Domain-Driven Design (DDD) e Clean Architecture, dividindo o software em:
* `agents/`: Motores de raciocínio (MAPPO), percepção e *Safety Guards*.
* `coordination/`: Despachante de controle e correlacionador de ACKs.
* `domain/`: Classes imutáveis (Proposals, Conflicts, Decisions).
* `e2/`: Decodificadores e Encoders específicos de KPM e RC (isolamento de ASN.1).
* `infrastructure/`: Clientes RMR, SDL (Redis), Subscription Manager e Config Manager.
* `observability/`: Métricas no padrão Prometheus (ex: `rdl_kpm_indications_total`), health e logs em JSON (Structlog).

## 4. Requisitos
* Python 3.10+ (ou ambiente via `uv`)
* Docker
* Ambiente O-RAN Near-RT RIC (Ex: FlexRIC) para testes End-to-End
* `dms_cli` para onboarding.

## 5. Instalação
Clone este repositório e instale as dependências:
```bash
git clone https://github.com/georgebarbosa3090/xApp-RDL-Resource-and-Decision-Layer-.git
cd xApp-RDL-Resource-and-Decision-Layer-

# Utilizando UV (recomendado) ou PIP:
uv venv --python 3.10
uv pip install -r requirements.txt
# Para ativar o motor de IA:
uv pip install -r requirements-ml.txt
```

## 6. Configuração
Toda a configuração é estrita e centralizada. Modifique o arquivo `configs/config-file.json` para alterar as credenciais do SDL, portos do RMR, e timers de controle. O `configs/schema.json` blinda a configuração contra erros de digitação.

## 7. Execução Local
A RDL pode ser inicializada localmente para desenvolvimento:
```bash
export USE_FAKE_SDL=true
export RMR_SEED_RT=configs/routes.rt
python src/main.py
```
A saúde do app pode ser verificada em `http://localhost:8080/health`.

## 8. Docker
O projeto possui um build determinístico, Non-root e Multi-stage.
```bash
make build
```
Isso gerará a imagem `iqos-xapp-rdl:1.1.0`. O container é seguro, utilizando um usuário focado (`xapp`) sem privilégios root.

## 9. Near-RT RIC
Para enviar a xApp para um ambiente RIC real, assegure-se de que o E2 Manager e o Subscription Manager estejam operando nas rotas definidas em `configs/routes.rt.template`. A RDL vai injetar sua requisição de Subscrição diretamente.

## 10. Onboarding
O empacotamento é nativamente aceito pelo `AppMgr`.
```bash
make onboard
```
*Isto engatilha o comando:* `dms_cli onboard configs/xapp_descriptor.json configs/schema.json`

## 11. Deployment
```bash
make install
```
A implantação no Kubernetes também pode ser testada manualmente através dos manifestos contidos em `deploy/kubernetes/`.

## 12. Testes
A suíte de testes unitários foi construída utilizando o `pytest`. Os mocks garantem que a inteligência artificial é testável sem acesso à rede RMR.
```bash
make test
```

## 13. Experimentos
O `scripts/collect_evidence.sh` automatiza as coletas para as baterias de cenários do projeto.
```bash
./scripts/collect_evidence.sh EXPERIMENTO_E1
```

## 14. Troubleshooting
Se os comandos não chegarem à rádio-base:
1. Verifique se a variável `USE_FAKE_SDL` está em `false` (produção exige Redis).
2. Veja as estatísticas do Prometheus na porta `:8081` (`rdl_control_failures_total`).
3. Leia os logs usando `make logs` (filtrando severidade `"level": "error"` no structlog).

## 15. Limitações
- O decodificador KPM atualmente opera uma validação binária leve devido à necessidade de bibliotecas C para a tradução APER estrita, requerendo a instalação paralela do *pycrate* nativo no SO hospedeiro em redes de produção.
- Conflitos de Recursos Dinâmicos (Resource) ainda são mapeados em grafos de proximidade, exigindo integração com simulador RAN para precisão milimétrica.

## 16. Roadmap
- [ ] Incorporar biblioteca O-RAN `asn1c` compilada nativamente ao Dockerfile.
- [ ] Implementar decodificação do O-RAN E2SM-RC v1.0.3 direta no RC_Encoder.
- [ ] Interface visual Web para observar o Knowledge Graph.

## 17. Referências
- Artigo base: *"Managing O-RAN Networks: xApp Development from Zero to Hero"*.
- Repositório: *https://github.com/georgebarbosa3090/xApp-RDL-Resource-and-Decision-Layer-*
