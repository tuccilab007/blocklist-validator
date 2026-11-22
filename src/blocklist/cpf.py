"""Utilitários de CPF: limpar, validar, formatar e mascarar.

São funções puras: não usam banco, planilha nem internet. Por isso são fáceis
de testar e podem ser reaproveitadas em qualquer módulo do projeto.
"""
import re


def normalizar_cpf(valor: object) -> str:
    """Devolve só os dígitos do CPF.

    - Texto: remove pontos, traço e espaços ("529.982.247-25" -> "52998224725").
      Não completamos zeros: um CPF digitado errado não pode virar válido.
    - Número (int/float): o Excel guarda CPF numérico sem o zero à esquerda,
      então devolvemos o zero até completar 11 dígitos.
    - Vazio (None ou NaN, como o pandas lê célula vazia): devolve "".
    """
    if valor is None:
        return ""
    if isinstance(valor, float):
        if valor != valor:  # NaN: único valor diferente de si mesmo
            return ""
        if valor.is_integer():
            valor = int(valor)
    if isinstance(valor, int):
        return re.sub(r"[^0-9]", "", str(valor)).zfill(11)
    return re.sub(r"[^0-9]", "", str(valor))


def cpf_valido(cpf: str) -> bool:
    """True se o CPF (já normalizado) tem 11 dígitos e dígitos verificadores corretos."""
    if not re.fullmatch(r"[0-9]{11}", cpf):
        return False
    # 11111111111 passa na conta dos dígitos, mas não é um CPF válido.
    if cpf == cpf[0] * 11:
        return False
    for tamanho in (9, 10):  # 1º dígito usa 9 números, 2º usa 10
        pesos = range(tamanho + 1, 1, -1)  # 10..2 e depois 11..2
        soma = sum(int(digito) * peso for digito, peso in zip(cpf[:tamanho], pesos))
        esperado = (soma * 10) % 11 % 10  # resto 10 vira 0
        if esperado != int(cpf[tamanho]):
            return False
    return True


def formatar_cpf(cpf: str) -> str:
    """52998224725 -> 529.982.247-25 (para exibir)."""
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def mascarar_cpf(cpf: str) -> str:
    """52998224725 -> ***.982.247-** (para logs: nunca registrar o CPF inteiro)."""
    if not re.fullmatch(r"[0-9]{11}", cpf):
        return "***"
    return f"***.{cpf[3:6]}.{cpf[6:9]}-**"