# Teste do xApp-RDL combinado com outra xApp no OpenRAN@Brasil Blueprint v3

## Objetivo

Este documento descreve um protocolo experimental para validar o
**xApp-RDL (Resource and Decision Layer)** em conjunto com outras xApps
utilizando o **OpenRAN@Brasil Blueprint v3**.

## Ambiente

-   OSC Near-RT RIC
-   Kubernetes
-   Docker
-   Helm
-   GUARA-ns
-   NORI/ns-3
-   KPM xApp
-   RC xApp

### Configuração recomendada

  Recurso          Valor
  --------- ------------
  vCPU            12--16
  RAM          24--32 GB
  Disco       150 GB SSD

## Arquitetura

``` text
OSC Near-RT RIC
 ├── KPM xApp
 ├── RC/RANSlicer xApp
 ├── xApp-RDL
 │    ├── Perception
 │    ├── Reasoning
 │    ├── Refinement
 │    └── Action Arbiter
 └── GUARA-ns / NORI
```

## Etapas

1.  Implantar GUARA-ns e NORI.
2.  Validar E2 Setup e KPM.
3.  Implantar xApp-RDL em modo observação.
4.  Implantar RC xApp.
5.  Duplicar RC (RC-A e RC-B) para gerar conflitos.
6.  Ativar arbitragem da RDL.
7.  Comparar sem RDL, prioridade estática e MAPPO.

## Métricas

### Rede

-   Throughput
-   Latência
-   PRB Usage
-   SLA Violations

### Coordenação

-   Conflitos detectados
-   Conflitos resolvidos
-   Ações rejeitadas

### Sistema

-   CPU
-   Memória
-   Latência da decisão
-   Tempo de inferência

## Evolução

1.  RDL + KPM
2.  RDL + RC
3.  RDL + RC-A + RC-B
4.  RDL + RANSlicer
5.  RDL + Energy xApp
6.  NORI multi-célula
7.  srsRAN
8.  Testbed OpenRAN@Brasil

## Critério de sucesso

-   Receber propostas das xApps.
-   Detectar conflitos.
-   Emitir apenas uma decisão final.
-   Reduzir conflitos frente ao baseline.
-   Registrar todas as métricas.
