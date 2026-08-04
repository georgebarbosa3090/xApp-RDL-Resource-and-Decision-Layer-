# Introdução à xApp RDL (Resource and Decision Layer)

Bem-vindo à documentação oficial da **xApp RDL**! Este documento foi feito para ser didático, ajudando pesquisadores, desenvolvedores e arquitetos de redes a entenderem não apenas o código, mas o **propósito** de cada componente deste projeto.

---

## O que é uma xApp?
No ecossistema **O-RAN (Open Radio Access Network)**, a rede de rádio (antenas, estações base) é aberta e programável. O "cérebro" que toma decisões rápidas sobre a rede de rádio é chamado de **Near-RT RIC** (Near-Real-Time RAN Intelligent Controller).
Uma **xApp** é simplesmente um aplicativo de software (como se fosse um app de celular) que roda dentro do Near-RT RIC. Cada xApp tem uma função específica, como otimizar o consumo de energia, gerenciar a qualidade de serviço (QoS) ou controlar o *handover* (troca de antenas por um celular).

## O Problema: Conflitos na Rede
Como o Near-RT RIC permite rodar múltiplas xApps criadas por empresas diferentes ao mesmo tempo, um problema grave surge: **Conflitos de Interesse**.
- A **xApp de Energia** pode decidir diminuir a potência da antena para economizar luz.
- Ao mesmo tempo, a **xApp de QoS** pode decidir aumentar a potência da antena para garantir que o usuário assista a um vídeo em 4K sem travar.

Se ambas enviarem seus comandos para a rede simultaneamente, a rede ficará instável.

## A Solução: xApp RDL
A **RDL (Resource and Decision Layer)** é uma xApp especial. Ela atua como um **Orquestrador Cognitivo** (um juiz inteligente). 
Em vez das outras xApps enviarem comandos diretamente para a rede, elas enviam "Propostas de Ação" para a RDL. A RDL analisa o cenário global da rede, prevê as consequências e **resolve o conflito**, enviando apenas a melhor ação possível para a rede.

---

## Como navegar nesta documentação?
Para entender a fundo como a RDL foi construída, dividimos a documentação nos seguintes tópicos:

1. [Arquitetura Geral](01_arquitetura.md): Como a RDL se conecta ao RIC e aos Bancos de Dados.
2. [Módulos Core](02_modulos_core.md): O coração do sistema (Percepção, Orquestração e Memória).
3. [Módulos de Inteligência Artificial](03_modulos_ia.md): Como usamos Aprendizado por Reforço (MAPPO) e Machine Learning Clássico (Scikit-learn) para decidir e validar.
4. [Comunicação e Protocolos (RIC)](04_comunicacao_ric.md): Decodificadores ASN.1, troca de mensagens via RMR e interações com a rede.
5. [Testes e CI](05_testes_e_ci.md): Como garantir que nada quebre ao modificar o código.
6. [Guia de Implantação](06_guia_de_implantacao.md): Como rodar o sistema localmente (Docker).

---

> **Dica:** Se você é um desenvolvedor Python que acabou de chegar, comece pelo arquivo `src/rdl_xapp.py` no código-fonte, acompanhado do guia [Módulos Core](02_modulos_core.md).
