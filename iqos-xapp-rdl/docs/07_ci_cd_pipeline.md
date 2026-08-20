# 07. Integração e Entrega Contínuas (CI/CD)

Este documento descreve a esteira de automação (CI/CD) sugerida para o repositório da xApp-RDL usando o **GitHub Actions**. O objetivo é garantir que o código, especialmente a lógica do MARL e do Knowledge Graph, não sofra regressões durante o desenvolvimento contínuo.

## 1. Arquitetura da Esteira

A esteira será executada automaticamente a cada *push* ou *pull request* para a branch `main`.

Ela contempla 3 passos principais (jobs):
1. **Linting & Formatting:** Valida padrões de escrita do Python (`flake8`).
2. **Unit Testing:** Roda a suíte de testes automáticos com `pytest` (cobrindo Perception, Reasoner, KG e MAPPO).
3. **Docker Build Check:** Valida se o build Multi-stage do container Docker está funcional, garantindo que o xApp ainda pode ser containerizado para o Kubernetes.

## 2. Implementação do GitHub Actions

Para ativar esta esteira no GitHub, crie um arquivo no caminho `.github/workflows/ci.yml` com o seguinte conteúdo:

```yaml
name: xApp-RDL CI Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python 3.10
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r iqos-xapp-rdl/requirements.txt
        pip install -r iqos-xapp-rdl/requirements-ml.txt
        pip install pytest flake8
        
    - name: Lint with flake8
      run: |
        flake8 iqos-xapp-rdl/src iqos-xapp-rdl/tests --count --select=E9,F63,F7,F82 --show-source --statistics
        
    - name: Run Unit Tests (pytest)
      env:
        PYTHONPATH: iqos-xapp-rdl
      run: |
        pytest iqos-xapp-rdl/tests -v

  docker-build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Test Docker Build
      run: |
        cd iqos-xapp-rdl
        docker build -t iqos-xapp-rdl:test -f docker/Dockerfile .
```
