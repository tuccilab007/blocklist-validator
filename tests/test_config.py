import pytest

from blocklist import config


def _definir_banco(monkeypatch, **extras):
    base = {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "demo",
        "DB_USER": "app",
        "DB_PASSWORD": "segredo",
    }
    base.update(extras)
    for chave, valor in base.items():
        monkeypatch.setenv(chave, valor)


def test_carregar_banco_le_as_variaveis(monkeypatch):
    _definir_banco(monkeypatch)
    banco = config.carregar_banco()
    assert banco.nome == "demo"
    assert banco.usuario == "app"
    assert banco.porta == 5432


def test_banco_sem_usuario_levanta_erro_claro(monkeypatch):
    _definir_banco(monkeypatch, DB_USER="")
    with pytest.raises(config.ConfigError, match="DB_USER"):
        config.carregar_banco()


def test_porta_invalida_levanta_erro(monkeypatch):
    _definir_banco(monkeypatch, DB_PORT="abc")
    with pytest.raises(config.ConfigError, match="DB_PORT"):
        config.carregar_banco()


def test_senha_nao_aparece_no_repr(monkeypatch):
    _definir_banco(monkeypatch, DB_PASSWORD="senha-super-secreta")
    banco = config.carregar_banco()
    assert "senha-super-secreta" not in repr(banco)


def test_nivel_log_invalido_levanta_erro(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "BARULHENTO")
    with pytest.raises(config.ConfigError, match="LOG_LEVEL"):
        config.nivel_log()


def test_nivel_log_aceita_minusculas(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "debug")
    assert config.nivel_log() == "DEBUG"