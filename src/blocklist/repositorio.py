"""Consultas ao banco que o porteiro (rules) precisa. Só leitura.

Regra de ouro: os valores SEMPRE entram como parâmetros (:cpf), nunca colados
no texto do SQL com f-string. É isso que impede SQL injection.
"""
from dataclasses import dataclass
from datetime import date

from sqlalchemy import text
from sqlalchemy.engine import Engine

from blocklist.cpf import mascarar_cpf
from blocklist.db import get_engine
from blocklist.logger import get_logger

log = get_logger(__name__)


@dataclass(frozen=True)
class Bloqueio:
    """Registro da blocklist da empresa."""

    motivo: str
    bloqueado_em: date


@dataclass(frozen=True)
class Passagem:
    """Uma passagem da pessoa pela empresa."""

    data_admissao: date
    data_desligamento: date | None  # None = ainda trabalha na empresa


def buscar_bloqueio(cpf: str, engine: Engine | None = None) -> Bloqueio | None:
    """Devolve o bloqueio do CPF, ou None se ele não está na blocklist."""
    engine = engine or get_engine()
    with engine.connect() as conexao:
        linha = conexao.execute(
            text("SELECT motivo, bloqueado_em FROM blocklist WHERE cpf = :cpf"),
            {"cpf": cpf},
        ).one_or_none()
    log.debug("Blocklist %s: %s", mascarar_cpf(cpf), "achou" if linha else "não achou")
    if linha is None:
        return None
    return Bloqueio(motivo=linha.motivo, bloqueado_em=linha.bloqueado_em)


def buscar_passagem_mais_recente(
    cpf: str, engine: Engine | None = None
) -> Passagem | None:
    """Devolve a passagem de admissão mais recente do CPF, ou None se nunca trabalhou.

    Regra de negócio decidida: só a passagem mais recente conta.
    """
    engine = engine or get_engine()
    with engine.connect() as conexao:
        linha = conexao.execute(
            text(
                "SELECT data_admissao, data_desligamento "
                "FROM funcionarios WHERE cpf = :cpf "
                "ORDER BY data_admissao DESC LIMIT 1"
            ),
            {"cpf": cpf},
        ).one_or_none()
    log.debug("Passagem %s: %s", mascarar_cpf(cpf), "achou" if linha else "não achou")
    if linha is None:
        return None
    return Passagem(
        data_admissao=linha.data_admissao,
        data_desligamento=linha.data_desligamento,
    )