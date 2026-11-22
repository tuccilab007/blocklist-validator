from datetime import date

import pytest

from blocklist.repositorio import Passagem, buscar_passagem_mais_recente
from blocklist.rules import dias_de_casa, eh_ex_funcionario_recente


@pytest.mark.parametrize(
    "admissao, desligamento, esperado",
    [
        (date(2026, 2, 1), date(2026, 5, 2), 90),
        (date(2026, 1, 5), date(2026, 3, 20), 74),
        (date(2026, 3, 1), date(2026, 3, 1), 0),  # entrou e saiu no mesmo dia
        (date(2026, 9, 1), None, None),  # ainda trabalha
    ],
)
def test_dias_de_casa(admissao, desligamento, esperado):
    assert dias_de_casa(Passagem(admissao, desligamento)) == esperado


@pytest.mark.parametrize(
    "passagem, esperado",
    [
        (Passagem(date(2026, 1, 5), date(2026, 3, 20)), True),  # 74 dias
        (Passagem(date(2026, 2, 1), date(2026, 5, 2)), True),  # 90 dias: limite conta
        (Passagem(date(2026, 2, 1), date(2026, 5, 3)), False),  # 91 dias
        (Passagem(date(2019, 3, 1), date(2024, 8, 30)), False),  # muito tempo de casa
        (Passagem(date(2026, 9, 1), None), False),  # ainda trabalha
        (Passagem(date(2026, 3, 1), date(2026, 3, 1)), True),  # 0 dias
        (None, False),  # nunca trabalhou
    ],
)
def test_eh_ex_funcionario_recente(passagem, esperado):
    assert eh_ex_funcionario_recente(passagem) is esperado


def test_limite_personalizado():
    passagem = Passagem(date(2026, 2, 1), date(2026, 5, 3))  # 91 dias
    assert eh_ex_funcionario_recente(passagem) is False
    assert eh_ex_funcionario_recente(passagem, limite_dias=120) is True


# Elenco do seed no banco real: junta seed + consulta + regra.
@pytest.mark.parametrize(
    "cpf, esperado",
    [
        ("52998224725", False),  # A: só blocklist, nunca foi funcionário
        ("11144477735", False),  # B: só blocklist
        ("12345678909", True),  # C: passagem de 43 dias
        ("24681357928", True),  # D: 74 dias
        ("13579246828", True),  # E: exatamente 90 dias
        ("31415926590", False),  # F: 91 dias
        ("27182818205", False),  # G: mais de 5 anos
        ("16180339805", False),  # H: ainda trabalha
        ("98765432100", False),  # I: passagem mais recente é longa
        ("11235813207", False),  # não está em nenhuma tabela
    ],
)
def test_elenco_do_seed(engine_real, cpf, esperado):
    passagem = buscar_passagem_mais_recente(cpf, engine_real)
    assert eh_ex_funcionario_recente(passagem) is esperado