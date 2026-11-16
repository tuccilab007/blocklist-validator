"""Logs centralizados: aparecem no terminal e ficam gravados em logs/blocklist.log.

Uso em qualquer módulo:
    from blocklist.logger import get_logger
    log = get_logger(__name__)
    log.info("Processando %s candidatos", total)
"""
import logging
from logging.handlers import RotatingFileHandler

from blocklist import config

_FORMATO = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_configurado = False


def configurar_logs() -> None:
    """Configura o logger raiz. Chamar várias vezes não duplica as linhas."""
    global _configurado
    if _configurado:
        return

    config.DIR_LOGS.mkdir(parents=True, exist_ok=True)
    formato = logging.Formatter(_FORMATO)

    console = logging.StreamHandler()
    console.setFormatter(formato)

    # Rotação: ao passar de ~1 MB cria um arquivo novo e guarda até 3 antigos.
    arquivo = RotatingFileHandler(
        config.DIR_LOGS / "blocklist.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    arquivo.setFormatter(formato)

    raiz = logging.getLogger()
    raiz.setLevel(config.nivel_log())
    raiz.addHandler(console)
    raiz.addHandler(arquivo)
    _configurado = True


def get_logger(nome: str) -> logging.Logger:
    """Devolve um logger já configurado. Use get_logger(__name__)."""
    configurar_logs()
    return logging.getLogger(nome)