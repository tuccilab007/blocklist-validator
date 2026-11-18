"""Executa arquivos .sql no banco do projeto, tudo ou nada (uma transação).

Uso (com o .venv ativo, na raiz do projeto):
    python -m blocklist.sql_runner sql\\01_schema.sql

Limites desta versão simples (suficientes para os nossos scripts):
- comentários só em linhas próprias, começando com "--";
- sem ponto e vírgula dentro de textos ou funções.
"""
import sys
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from blocklist import config
from blocklist.db import get_engine
from blocklist.logger import get_logger

log = get_logger(__name__)


def dividir_comandos(script: str) -> list[str]:
    """Quebra o texto do script em comandos SQL separados por ';'."""
    sem_comentarios = "\n".join(
        linha for linha in script.splitlines() if not linha.strip().startswith("--")
    )
    return [c.strip() for c in sem_comentarios.split(";") if c.strip()]


def executar_arquivo(caminho: Path) -> int:
    """Roda todos os comandos do arquivo numa única transação.

    Se um comando falhar, NADA é gravado (rollback). Devolve quantos comandos
    foram executados.
    """
    if not caminho.is_file():
        raise FileNotFoundError(f"Arquivo SQL não encontrado: {caminho}")

    comandos = dividir_comandos(caminho.read_text(encoding="utf-8"))
    log.info("Executando %s (%d comandos)", caminho.name, len(comandos))
    try:
        # engine.begin(): abre uma transação e faz commit ao final (ou rollback no erro)
        with get_engine().begin() as conexao:
            for comando in comandos:
                # exec_driver_sql envia o texto como está, sem interpretar ":" e "%"
                conexao.exec_driver_sql(comando)
    except SQLAlchemyError as erro:
        log.error(
            "Falha em %s, nada foi gravado (rollback): %s",
            caminho.name, getattr(erro, "orig", erro),
        )
        raise
    log.info("Concluído: %s", caminho.name)
    return len(comandos)


def main(argv: list[str] | None = None) -> int:
    argumentos = sys.argv[1:] if argv is None else argv
    if len(argumentos) != 1:
        print("Uso: python -m blocklist.sql_runner sql\\01_schema.sql")
        return 2

    caminho = Path(argumentos[0])
    if not caminho.is_absolute():
        caminho = config.RAIZ_PROJETO / caminho

    try:
        total = executar_arquivo(caminho)
    except (FileNotFoundError, SQLAlchemyError, config.ConfigError) as erro:
        log.error("%s", erro)
        return 1
    print(f"OK: {caminho.name} ({total} comandos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())