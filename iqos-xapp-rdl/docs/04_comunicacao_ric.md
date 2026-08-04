# Comunicação com o OSC Near-RT RIC

Este documento aborda a camada de "tradução e envio" de dados entre a nossa xApp, desenvolvida em Python, e os componentes base (escritos geralmente em C++) da O-RAN Alliance.

## O Framework: `ricxappframe`
A biblioteca `ricxappframe` simplifica a conexão da RDL com a arquitetura padrão.
Ao invés de programarmos *sockets UDP/TCP* do zero, configuramos a classe `Xapp`, que abstrai todo o **RMR** (RIC Message Router).

## 1. O Protocolo e a Carga: ASN.1 (APER)
O-RAN adota o formato **ASN.1** (Abstract Syntax Notation One) para envio de dados, compactado usando a regra APER (Aligned Packed Encoding Rules).
Isso significa que, se interceptarmos os dados, veremos apenas lixo binário.
A RDL usa o módulo `asn1_decoder.py` baseado na biblioteca open-source **PyCrate** para converter esses bytes compactados de volta em campos nomeados legíveis no padrão Service Models (E2SM).

## 2. RMR: Routing Manager e Mensagens
Toda mensagem RMR precisa de um ID numérico para o sistema saber o que fazer com ela. Estes estão definidos no arquivo `configs/xapp_descriptor.json`.

- **MENSAGENS RX (O que nós ouvimos - Entradas):**
  - `12050 (RIC_INDICATION)`: O srsRAN enviou as KPMs (relatórios de telemetria da antena).
  - `30000 (RDL_ACTION_PROPOSAL)`: (ID customizado) Uma outra xApp quer nos sugerir que modifiquemos algo na rede.
  - `12011 (RIC_CONTROL_ACK)`: A rede aceitou nossa ação com sucesso.
  - `12012 (RIC_CONTROL_FAILURE)`: A rede rejeitou nossa ação.

- **MENSAGENS TX (O que nós falamos - Saídas):**
  - `12010 (RIC_CONTROL_REQUEST)`: A RDL exige que a rádio-base altere algum comportamento (ex: Modifique a Potência).

## 3. O Fluxo de Controle Real
No arquivo `rdl_xapp.py`, observe o método `_send_control`.
Ele transforma nossa intenção de alteração e empurra os pacotes para o framework através do comando `self.xapp.rmr_send()`.
O RIC (especificamente o componente E2 Term) é o responsável por pegar esse pacote RMR e empurrá-lo para o protocolo **E2AP** da RAN.
