# Módulos Core do Sistema

Este diretório contém os guias detalhados sobre as lógicas centrais que operam dentro do diretório `src/`.

## 1. O Orquestrador: `rdl_xapp.py`
A classe `RDLxApp` é o "ponto de entrada" (main) do sistema.
Ela é a responsável por:
- Inicializar o framework `ricxappframe`.
- Ler as configurações do sistema (ex: usar banco emulado ou banco real).
- Subir o servidor de métricas.
- Dizer ao framework quais mensagens ela quer ouvir (registrando *callbacks*).

**Exemplo de Callback:**
Quando uma mensagem KPM chega da rádio-base, o framework chama o método `_kpm_indication_handler`. Esse método desempacota a mensagem binária e manda os dados numéricos para a Percepção.

## 2. A Percepção: `perception_agent.py`
Imagine a percepção como a visão e audição do sistema.
Sua função principal é manter o estado atual da rede atualizado (através dos relatórios KPM) e alertar caso haja perigo iminente.

**Detecção de Conflitos:**
A RDL categoriza conflitos em dois tipos usando grafos de dependência (`NetworkX`):
- **Conflito Direto:** Duas xApps tentam modificar o MESMO parâmetro (Ex: xApp1 quer Potência = 10; xApp2 quer Potência = 20).
- **Conflito Indireto:** Duas xApps modificam parâmetros DIFERENTES, mas ambos afetam o MESMO indicador final. (Ex: xApp1 muda a modulação e xApp2 reduz blocos de rádio; ambas as coisas afetam a taxa de download (Throughput)).

## 3. O Historiador: `memory_module.py`
Nós não queremos que a Inteligência Artificial gaste poder computacional para decidir algo que já foi decidido com sucesso no passado.
O Módulo de Memória armazena os cenários em um Grafo de Conhecimento (usando a linguagem *Cypher* com **Neo4j/Memgraph**).
Se um conflito idêntico acontecer novamente em menos de 10 minutos, o Módulo de Memória devolve a resposta pré-calculada, poupando a CPU da RAN.

## 4. O Corretor de Sintaxe: `conflict_types.py`
Este não é um módulo de inteligência, mas é crítico. Aqui, usando `dataclasses` nativas do Python, nós definimos exatamente como os objetos transitam no sistema.
É aqui que definimos os _Enums_ (tipos restritos) como `ConflictType.DIRECT`, assegurando que o código inteiro fale a mesma língua e não cometa erros de digitação ao repassar informações entre si.
