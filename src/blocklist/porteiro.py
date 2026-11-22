"""O porteiro: junta CPF, banco e regras e devolve UMA decisão por candidato.

Ordem das verificações (a ordem é a precedência):
    1. CPF inválido        -> CPF_INVALIDO   (erro de dado, nem consulta o banco)
    2. Está na blocklist   -> BLOQUEIO_EMPRESA
    3. Ex-funcionário com 90 dias de casa ou menos (passagem mais recente)
                           -> EX_FUNCIONARIO_RECENTE
    4. Nenhuma restrição   -> APROVADO

O bloqueio da empresa vem antes do ex-funcionário: é uma decisão deliberada da
empresa, mais forte do que a regra de tempo de casa.

Se o banco falhar, o erro SOBE para quem chamou. O porteiro nunca aprova nem
reprova "no chute" quando não conseguiu consultar (falhar de forma segura).
"""
from dataclasses import dataclass
from enum import Enum

from blocklist import rules
from blocklist.cpf import cpf_valido, mascarar_cpf, normalizar_cpf
from blocklist.logger import get_logger
from blocklist.repositorio import buscar_bloqueio, buscar_passagem_mais_recente

log = get_logger(__name__)


class Desfecho(str, Enum):
    """Por que o candidato recebeu aquela resposta (código estável)."""

    APROVADO = "APROVADO"
    BLOQUEIO_EMPRESA = "BLOQUEIO_EMPRESA"
    EX_FUNCIONARIO_RECENTE = "EX_FUNCIONARIO_RECENTE"
    CPF_INVALIDO = "CPF_INVALIDO"


# O status é o que aparece na planilha: APROVADO, REPROVADO ou INVALIDO.
_STATUS = {
    Desfecho.APROVADO: "APROVADO",
    Desfecho.BLOQUEIO_EMPRESA: "REPROVADO",
    Desfecho.EX_FUNCIONARIO_RECENTE: "REPROVADO",
    Desfecho.CPF_INVALIDO: "INVALIDO",
}


@dataclass(frozen=True)
class Resultado:
    """A decisão do porteiro."""

    cpf: str  # só dígitos ("" se vazio)
    desfecho: Desfecho
    motivo: str  # texto para humanos

    @property
    def status(self) -> str:
        return _STATUS[self.desfecho]


def _decidir(cpf, consultar_bloqueio, consultar_passagem) -> Resultado:
    if not cpf_valido(cpf):
        return Resultado(cpf, Desfecho.CPF_INVALIDO, "CPF inválido: confira os 11 dígitos")

    bloqueio = consultar_bloqueio(cpf)
    if bloqueio is not None:
        data = bloqueio.bloqueado_em.strftime("%d/%m/%Y")
        return Resultado(
            cpf,
            Desfecho.BLOQUEIO_EMPRESA,
            f"Bloqueado pela empresa em {data}: {bloqueio.motivo}",
        )

    passagem = consultar_passagem(cpf)
    if rules.eh_ex_funcionario_recente(passagem):
        dias = rules.dias_de_casa(passagem)
        return Resultado(
            cpf,
            Desfecho.EX_FUNCIONARIO_RECENTE,
            f"Ex-funcionário com {dias} dias de casa "
            f"(limite: {rules.LIMITE_DIAS_EX_FUNCIONARIO} dias)",
        )

    return Resultado(cpf, Desfecho.APROVADO, "Nenhuma restrição encontrada")


def validar_candidato(
    cpf_bruto: object,
    *,
    consultar_bloqueio=buscar_bloqueio,
    consultar_passagem=buscar_passagem_mais_recente,
) -> Resultado:
    """Valida um candidato pelo CPF (com ou sem pontuação) e devolve a decisão.

    As duas funções de consulta podem ser trocadas (nos testes usamos versões
    falsas, sem banco).
    """
    cpf = normalizar_cpf(cpf_bruto)
    resultado = _decidir(cpf, consultar_bloqueio, consultar_passagem)
    log.info("CPF %s -> %s", mascarar_cpf(cpf), resultado.desfecho.value)
    return resultado