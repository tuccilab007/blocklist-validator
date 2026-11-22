"""Regras de negócio do validador, uma por função.

São funções puras: recebem dados já prontos e devolvem uma resposta. Não
consultam banco, planilha nem internet, então são fáceis de testar.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # só para o editor; evita puxar o banco na hora de importar
    from blocklist.repositorio import Passagem

# "3 meses ou menos" foi definido como 90 dias corridos.
LIMITE_DIAS_EX_FUNCIONARIO = 90


def dias_de_casa(passagem: Passagem) -> int | None:
    """Dias corridos entre a admissão e o desligamento.

    Conta desligamento menos admissão (1 de fev a 2 de mai = 90 dias).
    Devolve None se a pessoa ainda trabalha na empresa.
    """
    if passagem.data_desligamento is None:
        return None
    return (passagem.data_desligamento - passagem.data_admissao).days


def eh_ex_funcionario_recente(
    passagem: Passagem | None,
    limite_dias: int = LIMITE_DIAS_EX_FUNCIONARIO,
) -> bool:
    """True se a passagem foi curta: saiu com `limite_dias` de casa ou menos.

    - Nunca trabalhou na empresa (None): False.
    - Ainda trabalha (sem desligamento): False, porque não é ex-funcionário.
    - O limite conta: exatamente 90 dias ainda é "recente".
    """
    if passagem is None:
        return False
    dias = dias_de_casa(passagem)
    if dias is None:
        return False
    return dias <= limite_dias