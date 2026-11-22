import pytest

from blocklist.cpf import cpf_valido, formatar_cpf, mascarar_cpf, normalizar_cpf

CPFS_DO_SEED = [
    "52998224725",
    "11144477735",
    "12345678909",
    "24681357928",
    "13579246828",
    "31415926590",
    "27182818205",
    "16180339805",
    "98765432100",
]


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("529.982.247-25", "52998224725"),
        (" 52998224725 ", "52998224725"),
        ("529 982 247 25", "52998224725"),
        ("abc", ""),
        (None, ""),
        (float("nan"), ""),
        (52998224725, "52998224725"),
        (52998224725.0, "52998224725"),
        (1234567890, "01234567890"),  # Excel perdeu o zero à esquerda
    ],
)
def test_normalizar_cpf(entrada, esperado):
    assert normalizar_cpf(entrada) == esperado


@pytest.mark.parametrize("cpf", CPFS_DO_SEED + ["11235813207"])
def test_cpfs_corretos_sao_validos(cpf):
    assert cpf_valido(cpf) is True


@pytest.mark.parametrize(
    "cpf",
    [
        "52998224724",  # 2º dígito errado
        "52998224735",  # 1º dígito errado
        "11111111111",  # todos iguais
        "00000000000",
        "1234567890",  # 10 dígitos
        "529982247250",  # 12 dígitos
        "",
        "5299822472a",  # tem letra
        "529.982.247-25",  # não normalizado: a validação exige só dígitos
    ],
)
def test_cpfs_incorretos_sao_invalidos(cpf):
    assert cpf_valido(cpf) is False


def test_formatar_cpf():
    assert formatar_cpf("52998224725") == "529.982.247-25"


@pytest.mark.parametrize(
    "cpf, esperado",
    [("52998224725", "***.982.247-**"), ("123", "***"), ("", "***")],
)
def test_mascarar_cpf(cpf, esperado):
    assert mascarar_cpf(cpf) == esperado