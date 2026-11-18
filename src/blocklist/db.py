"""Conexão com o PostgreSQL (SQLAlchemy 2.x + psycopg 3).

Uso:
    from blocklist.db import get_engine
    with get_engine().connect() as conn:
        ...

Teste rápido de conexão (com o .venv ativo):
    python -m blocklist.db
"""
import sys
import time
from functools import lru_cache

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, Engine
from sqlalchemy.exc import OperationalError

from blocklist import config
from blocklist.logger import get_logger

log = get_logger(__name__)


class ConexaoError(Exception):
    """Não foi possível conectar ao banco depois de todas as tentativas."""


def montar_url(banco: config.Banco) -> URL:
    """Monta a URL de conexão.

    URL.create escapa caracteres especiais da senha (@, :, / ...), coisa que
    um f-string simples não faria.
    """
    return URL.create(
        drivername="postgresql+psycopg",  # psycopg 3
        username=banco.usuario,
        password=banco.senha,
        host=banco.host,
        port=banco.porta,
        database=banco.nome,
    )


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Cria (uma única vez) o engine, que gerencia o pool de conexões."""
    banco = config.carregar_banco()
    # Atenção: nunca registrar a senha no log.
    log.info(
        "Preparando conexão: %s@%s:%s/%s",
        banco.usuario, banco.host, banco.porta, banco.nome,
    )
    # pool_pre_ping testa a conexão antes de usá-la e recria se ela caiu.
    return create_engine(montar_url(banco), pool_pre_ping=True)


def _resumo_erro(erro: Exception) -> str:
    """Primeira linha do erro original do driver (sem textão do SQLAlchemy)."""
    original = getattr(erro, "orig", None) or erro
    linhas = [ln.strip() for ln in str(original).splitlines() if ln.strip()]
    return linhas[0] if linhas else type(original).__name__


def testar_conexao(tentativas: int = 3, espera: float = 2.0) -> dict:
    """Tenta conectar e rodar um SELECT simples, com retentativas.

    Devolve {"usuario": ..., "banco": ...}. Se todas as tentativas falharem,
    levanta ConexaoError.
    """
    ultimo_erro = None
    for numero in range(1, tentativas + 1):
        try:
            with get_engine().connect() as conexao:
                usuario, banco = conexao.execute(
                    text("SELECT current_user, current_database()")
                ).one()
            log.info(
                "Conexão OK (tentativa %d): usuario=%s banco=%s",
                numero, usuario, banco,
            )
            return {"usuario": usuario, "banco": banco}
        except OperationalError as erro:
            ultimo_erro = erro
            log.warning(
                "Falha ao conectar (tentativa %d/%d): %s",
                numero, tentativas, _resumo_erro(erro),
            )
            if numero < tentativas:
                time.sleep(espera)
    raise ConexaoError(
        f"Sem conexão após {tentativas} tentativas: {_resumo_erro(ultimo_erro)}"
    ) from ultimo_erro


def main() -> int:
    try:
        info = testar_conexao()
    except (ConexaoError, config.ConfigError) as erro:
        log.error("%s", erro)
        return 1
    print(f"Conectado como {info['usuario']} no banco {info['banco']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())