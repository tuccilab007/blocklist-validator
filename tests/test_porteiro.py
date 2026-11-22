from datetime import date

import pytest

from blocklist.porteiro import Desfecho, Resultado, validar_candidato
from blocklist.repositorio import Bloqueio, Passagem

CPF_A = "52998224725"  # na blocklist
CPF_C = "12345678909"  # na blocklist E com passagem de 43 dias


class _Consultas:
    """Consultas falsas (sem banco) que também registram quem foi consultado."""

    def __init__(self, bloqueios=None, passagens=None):
        self._bloqueios = bloqueios or {}
        self._passagens = passagens or {}
        self.chamadas_bloqueio = []
        self.chamadas_passagem = []

    def bloqueio(self, cpf):
        self.chamadas_bloqueio.append(cpf)
        return self._bloqueios.get(cpf)

    def passagem(self, cpf):
        self.chamadas_passagem.append(cpf)
        return self._passagens.get(cpf)


def _validar(cpf, consultas):
    return validar_candidato(
        cpf,
        consultar_bloqueio=consultas.bloqueio,
        consultar_passagem=consultas.passagem,
    )


def test_cpf_invalido_nem_consulta_o_banco():
    consultas = _Consultas()
    resultado = _validar("111.111.111-11", consultas)
    assert resultado.desfecho is Desfecho.CPF_INVALIDO
    assert resultado.status == "INVALIDO"
    assert consultas.chamadas_bloqueio == []
    assert consultas.chamadas_passagem == []


@pytest.mark.parametrize("entrada", ["", None, "abc"])
def test_cpf_vazio_ou_sem_numeros_e_invalido(entrada):
    assert _validar(entrada, _Consultas()).desfecho is Desfecho.CPF_INVALIDO


def test_cpf_na_blocklist_e_reprovado_com_o_motivo():
    consultas = _Consultas(bloqueios={CPF_A: Bloqueio("Mau comportamento", date(2024, 3, 12))})
    resultado = _validar(CPF_A, consultas)
    assert resultado.desfecho is Desfecho.BLOQUEIO_EMPRESA
    assert resultado.status == "REPROVADO"
    assert "Mau comportamento" in resultado.motivo
    assert "12/03/2024" in resultado.motivo


def test_bloqueio_vence_ex_funcionario_recente():
    consultas = _Consultas(
        bloqueios={CPF_C: Bloqueio("Acordo interno", date(2025, 8, 4))},
        passagens={CPF_C: Passagem(date(2025, 6, 2), date(2025, 7, 15))},  # 43 dias
    )
    resultado = _validar(CPF_C, consultas)
    assert resultado.desfecho is Desfecho.BLOQUEIO_EMPRESA
    # Como o bloqueio já decidiu, a passagem nem precisou ser consultada.
    assert consultas.chamadas_passagem == []


def test_ex_funcionario_recente_e_reprovado_com_os_dias_no_motivo():
    consultas = _Consultas(passagens={CPF_A: Passagem(date(2026, 1, 5), date(2026, 3, 20))})
    resultado = _validar(CPF_A, consultas)
    assert resultado.desfecho is Desfecho.EX_FUNCIONARIO_RECENTE
    assert resultado.status == "REPROVADO"
    assert "74 dias" in resultado.motivo


@pytest.mark.parametrize(
    "desligamento, desfecho_esperado",
    [
        (date(2026, 5, 2), Desfecho.EX_FUNCIONARIO_RECENTE),  # 90 dias: reprova
        (date(2026, 5, 3), Desfecho.APROVADO),  # 91 dias: aprova
    ],
)
def test_fronteira_de_90_dias(desligamento, desfecho_esperado):
    consultas = _Consultas(passagens={CPF_A: Passagem(date(2026, 2, 1), desligamento)})
    assert _validar(CPF_A, consultas).desfecho is desfecho_esperado


def test_quem_ainda_trabalha_e_aprovado():
    consultas = _Consultas(passagens={CPF_A: Passagem(date(2026, 9, 1), None)})
    assert _validar(CPF_A, consultas).desfecho is Desfecho.APROVADO


def test_quem_nunca_trabalhou_e_aprovado():
    resultado = _validar(CPF_A, _Consultas())
    assert resultado.desfecho is Desfecho.APROVADO
    assert resultado.status == "APROVADO"


@pytest.mark.parametrize("entrada", ["529.982.247-25", "52998224725", 52998224725])
def test_aceita_cpf_com_pontuacao_sem_pontuacao_ou_numero(entrada):
    consultas = _Consultas(bloqueios={CPF_A: Bloqueio("Mau comportamento", date(2024, 3, 12))})
    resultado = _validar(entrada, consultas)
    assert resultado.cpf == CPF_A
    assert resultado.desfecho is Desfecho.BLOQUEIO_EMPRESA


def test_falha_do_banco_sobe_em_vez_de_virar_decisao():
    def banco_fora_do_ar(cpf):
        raise RuntimeError("banco fora do ar")

    with pytest.raises(RuntimeError, match="banco fora do ar"):
        validar_candidato(
            CPF_A,
            consultar_bloqueio=banco_fora_do_ar,
            consultar_passagem=_Consultas().passagem,
        )


@pytest.mark.parametrize(
    "desfecho, status",
    [
        (Desfecho.APROVADO, "APROVADO"),
        (Desfecho.BLOQUEIO_EMPRESA, "REPROVADO"),
        (Desfecho.EX_FUNCIONARIO_RECENTE, "REPROVADO"),
        (Desfecho.CPF_INVALIDO, "INVALIDO"),
    ],
)
def test_status_de_cada_desfecho(desfecho, status):
    assert Resultado(cpf="", desfecho=desfecho, motivo="x").status == status


# Elenco do seed no PostgreSQL real: seed + consultas + regras + porteiro juntos.
@pytest.mark.parametrize(
    "cpf, status, desfecho",
    [
        ("529.982.247-25", "REPROVADO", Desfecho.BLOQUEIO_EMPRESA),  # A
        ("111.444.777-35", "REPROVADO", Desfecho.BLOQUEIO_EMPRESA),  # B
        ("123.456.789-09", "REPROVADO", Desfecho.BLOQUEIO_EMPRESA),  # C: bloqueio vence
        ("246.813.579-28", "REPROVADO", Desfecho.EX_FUNCIONARIO_RECENTE),  # D: 74 dias
        ("135.792.468-28", "REPROVADO", Desfecho.EX_FUNCIONARIO_RECENTE),  # E: 90 dias
        ("314.159.265-90", "APROVADO", Desfecho.APROVADO),  # F: 91 dias
        ("271.828.182-05", "APROVADO", Desfecho.APROVADO),  # G: muito tempo de casa
        ("161.803.398-05", "APROVADO", Desfecho.APROVADO),  # H: ainda trabalha
        ("987.654.321-00", "APROVADO", Desfecho.APROVADO),  # I: passagem recente longa
        ("112.358.132-07", "APROVADO", Desfecho.APROVADO),  # fora das duas tabelas
        ("111.111.111-11", "INVALIDO", Desfecho.CPF_INVALIDO),  # dígitos todos iguais
    ],
)
def test_elenco_do_seed_no_banco_real(engine_real, cpf, status, desfecho):
    resultado = validar_candidato(cpf)
    assert resultado.status == status
    assert resultado.desfecho is desfecho