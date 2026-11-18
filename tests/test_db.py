import pytest
from sqlalchemy.exc import OperationalError

from blocklist import config, db


def _banco(senha="segredo"):
    return config.Banco(
        host="localhost", porta=5432, nome="demo", usuario="app", senha=senha
    )


def test_montar_url_usa_driver_psycopg_3():
    url = db.montar_url(_banco())
    assert url.drivername == "postgresql+psycopg"
    assert url.database == "demo"
    assert url.username == "app"


def test_montar_url_escapa_caracteres_especiais_da_senha():
    url = db.montar_url(_banco(senha="p@ss:word"))
    assert url.password == "p@ss:word"
    assert "p%40ss%3Aword" in url.render_as_string(hide_password=False)


def test_url_esconde_a_senha_por_padrao():
    url = db.montar_url(_banco(senha="senha-super-secreta"))
    assert "senha-super-secreta" not in url.render_as_string()


class _EngineQueFalha:
    def __init__(self):
        self.chamadas = 0

    def connect(self):
        self.chamadas += 1
        raise OperationalError("SELECT 1", {}, Exception("conexão recusada"))


def test_testar_conexao_tenta_n_vezes_e_depois_levanta_erro(monkeypatch):
    engine_falso = _EngineQueFalha()
    monkeypatch.setattr(db, "get_engine", lambda: engine_falso)
    monkeypatch.setattr(db.time, "sleep", lambda segundos: None)  # sem esperar

    with pytest.raises(db.ConexaoError, match="3 tentativas"):
        db.testar_conexao(tentativas=3, espera=0)

    assert engine_falso.chamadas == 3