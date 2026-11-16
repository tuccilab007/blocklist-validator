"""Verifica se o ambiente está pronto para o projeto blocklist-validator.

Como rodar (terminal integrado do VS Code, com o .venv ativo):
    python verificar_ambiente.py
"""
import importlib
import importlib.util
import logging
import shutil
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(message)s")
log = logging.getLogger("verificar_ambiente")

# módulo importável -> nome do pacote no pip
PACOTES = {
    "pandas": "pandas",
    "openpyxl": "openpyxl",
    "playwright": "playwright",
    "sqlalchemy": "SQLAlchemy",
    "psycopg": "psycopg[binary]",
    "flask": "Flask",
    "dotenv": "python-dotenv",
    "pytest": "pytest",
}
FERRAMENTAS_OBRIGATORIAS = ["git"]
FERRAMENTAS_OPCIONAIS = ["psql", "node"]  # ajudam, mas o projeto roda sem elas


def resumo_erro(erro: Exception, limite: int = 200) -> str:
    """Primeira linha útil do erro (o Playwright costuma despejar um textão)."""
    for linha in str(erro).splitlines():
        if linha.strip():
            return linha.strip()[:limite]
    return type(erro).__name__


def checar_python() -> bool:
    versao = sys.version_info
    ok = versao >= (3, 10)
    log.info("%s Python %d.%d.%d", "OK    " if ok else "FALTA ", *versao[:3])
    if not ok:
        log.warning("Use Python 3.10 ou superior.")
    return ok


def checar_venv() -> bool:
    ativo = sys.prefix != sys.base_prefix
    log.info("%s ambiente virtual (.venv) ativo", "OK    " if ativo else "AVISO ")
    if not ativo:
        log.warning("Crie e selecione o .venv: python -m venv .venv")
    return ativo


def checar_pacotes() -> bool:
    tudo_ok = True
    for modulo, pacote in PACOTES.items():
        try:
            importlib.import_module(modulo)
            log.info("OK     pacote %s", pacote)
        except ImportError:
            tudo_ok = False
            log.error("FALTA  pacote %s -> python -m pip install %s", pacote, pacote)
    return tudo_ok


def checar_ferramentas() -> bool:
    tudo_ok = True
    for nome in FERRAMENTAS_OBRIGATORIAS + FERRAMENTAS_OPCIONAIS:
        obrigatoria = nome in FERRAMENTAS_OBRIGATORIAS
        caminho = shutil.which(nome)
        if caminho:
            saida = subprocess.run(
                [caminho, "--version"], capture_output=True, text=True, check=False
            ).stdout.strip()
            log.info("OK     %s (%s)", nome, saida)
        elif obrigatoria:
            tudo_ok = False
            log.error("FALTA  %s não encontrado no PATH", nome)
        else:
            log.warning("AVISO  %s não encontrado no PATH (opcional)", nome)
    return tudo_ok


def _abrir_e_fechar(playwright, **opcoes) -> None:
    navegador = playwright.chromium.launch(headless=True, **opcoes)
    navegador.close()


def checar_navegador_playwright() -> bool:
    """Tenta o Chromium do Playwright; se falhar, tenta o Edge instalado."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        try:
            _abrir_e_fechar(p)
            log.info("OK     Playwright abre o Chromium")
            return True
        except Exception as erro:  # noqa: BLE001 - qualquer falha interessa
            log.warning("AVISO  Chromium do Playwright não abriu: %s", resumo_erro(erro))

        try:
            _abrir_e_fechar(p, channel="msedge")
            log.warning(
                "AVISO  Edge abriu. No projeto, use launch(channel='msedge')."
            )
            return True
        except Exception as erro:  # noqa: BLE001
            log.error("FALTA  Edge também não abriu: %s", resumo_erro(erro))
            log.error("Tente: python -m playwright install chromium")
            return False


def main() -> int:
    resultados = [
        checar_python(),
        checar_venv(),
        checar_pacotes(),
        checar_ferramentas(),
    ]
    # só tenta abrir o navegador se o pacote existe
    if importlib.util.find_spec("playwright"):
        resultados.append(checar_navegador_playwright())
    if all(resultados):
        log.info("Ambiente pronto.")
        return 0
    log.error("Ambiente incompleto. Corrija os itens acima e rode de novo.")
    return 1


if __name__ == "__main__":
    sys.exit(main())