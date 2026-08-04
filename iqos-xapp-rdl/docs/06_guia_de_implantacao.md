# Guia de Implantação e Execução

O projeto xApp RDL (Resource and Decision Layer) foi empacotado para ser executado como um contêiner no ecossistema do OSC Near-RT RIC, mas também para rodar com Mocks e bancos de dados locais durante o desenvolvimento.

## Variáveis de Ambiente Críticas
A classe `RDLxApp` ajusta seu comportamento com base nas variáveis presentes na execução.
- `USE_FAKE_SDL`: (Default: True). O Shared Data Layer real do OSC Near-RT RIC usa instâncias de Redis remotas. Ao deixar em `True`, ativamos o mock de dicionário Python do `ricxappframe`, poupando a configuração pesada do Redis localmente.

## Configuração `configs/xapp_descriptor.json`
Toda xApp no ecossistema da *O-RAN Software Community (OSC)* deve estar empacotada com um descritor. É um arquivo JSON que define a "identidade" da aplicação perante a rede, suas métricas (Prometheus) e portas abertas.
Nele, você encontrará as portas:
- `8080` (HTTP) - Porta padrão de saúde (healthcheck)
- `8081` (Prometheus) - Porta das nossas métricas KPM e de Conflitos
- `4560` (RMR) - Porta de entrada de dados

## Executando com Docker Compose (Local)
Para testar a xApp sem um RIC real e rodar o nosso Banco de Grafos, utilize o Docker. Nós escrevemos o `docker-compose.yml` que sobe o servidor gráfico do **Memgraph** junto com a nossa xApp.

**Passo a passo:**
1. Tenha o `Docker Desktop` instalado no Windows/Mac, ou `docker-compose` no Linux.
2. Abra o terminal na pasta raiz do projeto.
3. Crie a imagem (Build):
   ```bash
   cd docker
   docker-compose build
   ```
4. Suba o ambiente (Up):
   ```bash
   docker-compose up
   ```

A xApp vai começar a cuspir *Logs* coloridos do `structlog` informando que está ouvindo a porta RMR e conectada ao Memgraph (host: `memgraph` na porta `7687`).

## Implantando no OSC Near-RT RIC (Produção)
Para implantação real (Ex: no Release J da OSC ou no FlexRIC):
1. Você envia o contêiner gerado pelo Dockerfile para o seu Docker Hub ou Harbor (Registro de contêineres). Ex: `muriloavlis/iqos-xapp:latest`.
2. Você utiliza a ferramenta CLI de gerência do RIC (`dms_cli` do *Deployment Management Service*) para "onboardar" a xApp, enviando para ela o nosso `configs/xapp_descriptor.json`.
3. O Kubernetes interno do RIC irá baixar o contêiner e orquestrar as ligações de rede internas, criando o pod na porta 4560 (RMR) de forma invisível.
