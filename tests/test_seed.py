import re

from blocklist import config
from blocklist.sql_runner import dividir_comandos


def _texto_seed() -> str:
    return (config.DIR_SQL / "02_seed.sql").read_text(encoding="utf-8")


def test_seed_tem_dois_inserts_idempotentes():
    comandos = dividir_comandos(_texto_seed())
    assert len(comandos) == 2
    for comando in comandos:
        assert comando.startswith("INSERT INTO")
        assert "ON CONFLICT" in comando
        assert "DO NOTHING" in comando


def test_seed_cpfs_tem_11_digitos():
    cpfs = re.findall(r"'([0-9]+)'", _texto_seed())
    assert cpfs, "nenhum CPF encontrado no seed"
    assert all(len(cpf) == 11 for cpf in cpfs)