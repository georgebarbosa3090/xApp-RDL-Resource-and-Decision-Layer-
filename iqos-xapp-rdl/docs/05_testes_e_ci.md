# Testes e CI (Continuous Integration)

Como estipulado pelo padrão O-RAN Zero to Hero, o nível de cobertura global alvo é `>= 80%`.

## 1. Testes Automatizados com Pytest (`tests/`)
Nós testamos as regras de negócio de forma agnóstica à rede (não rodamos a xApp completa conectada para testar o MAPPO, nós isolamos e "Mockamos" a API RMR usando `unittest.mock`).

Para rodar (supondo ambiente Python local):
```bash
make test
```
*(O comando fará com que o PYTHONPATH seja injetado corretamente na pasta raiz).*

## 2. Validação Estática e de Descriptor
Não queremos mandar uma xApp para o RIC que falha na sintaxe do arquivo de *onboarding*.
Criamos validação JSON Schema Draft-07 estrita e um Makefile correspondente:
```bash
make validate
```
Isto assegura que o arquivo `configs/xapp_descriptor.json` está totalmente em compliance e pronto para uso no AppMgr.

## 3. Coleta de Evidências Experimentais
O artigo O-RAN determina experimentos do cenário E1 ao E6 (Baseline sem RDL, prioridade fixa, MAPPO, injeção de falhas, etc).
Implementamos o script de coleta que agrupa magicamente os logs em pastas nomeadas:
```bash
./scripts/collect_evidence.sh EXPERIMENTO_E1
```
Esse comando agrupará:
- `metadata.json`
- `configuration.yaml`
- `container_image.txt`
- `kubectl_get_pods.txt`
- `xapp_logs.jsonl`

Isso permite gerar publicações acadêmicas com reprodutibilidade cravada em log, extraindo exatamente a taxa de SLA Violations e Falsos Negativos do sistema.
