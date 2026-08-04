# Testes e CI (Continuous Integration)

O mundo O-RAN é cheio de módulos interligados, tornando fácil quebrar a xApp com um código mal implementado. Para mitigar isso, nós configuramos uma suíte completa de testes usando **Pytest** e **GitHub Actions**.

## O Módulo `tests/`
Usamos TDD (*Test-Driven Development*) ou testes pós-funcionais isolados. 
Não rodamos a xApp completa conectada à rede durante um teste, mas sim **mockamos** (falseamos) a conexão usando a biblioteca `unittest.mock.MagicMock`.

**O que estamos testando agora?**
1. `test_agents.py`: Testa se a `Perception` percebe que "xApp_1" quer alterar PRB e "xApp_2" quer alterar PRB (mesmo parâmetro), lançando um `Conflito Direto`.
2. `test_reasoning.py`: Testa se a xApp de maior prioridade vai de fato ser coroada a vencedora do embate pela RDL.
3. `test_refinement.py`: Envia lixo intencional (valores foras do escopo) e verifica se a RDL os bloqueia.
4. `test_xapp_core.py`: Envia uma requisição RMR falsa simulando outra xApp e afirma (Assert) que a RDL respondeu usando o método de envio E2 Control (`12010`).

## Rodando Localmente
Se você estiver no ambiente de desenvolvimento, rode no seu terminal (requer as dependências instaladas no virtualenv, idealmente gerido pelo `uv`):

```bash
# Na raiz do projeto:
$env:PYTHONPATH="."  # Se no Windows PowerShell
pytest tests/ -v
```
A opção `-v` deixa os resultados coloridos e fáceis de ler (indicando PASS ou FAIL).

## O GitHub Actions (`.github/workflows/ci.yml`)
Configuramos a Integração Contínua para que, toda vez que um novo desenvolvedor der _push_ no repositório (ex: na branch `main`), uma máquina virtual na nuvem do GitHub seja criada:
1. Ela baixa o Ubuntu (Linux) com Python 3.10.
2. Instala os pacotes garantindo **versões travadas e blindadas** a falhas descritas no `requirements.txt`.
3. Roda todos os *Pytests*.
4. Se todos os testes passarem, ela simula (Dry-Run) a construção da nossa imagem Docker.
Se tudo ficar "Verde", o código é confiável.
