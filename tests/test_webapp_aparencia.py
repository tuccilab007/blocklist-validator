import pytest

from blocklist.config import ConfigError
from blocklist.porteiro import Desfecho, Resultado
from blocklist.webapp.app import create_app


def _html_do_resultado(resultado):
    cliente = create_app(lambda cpf: resultado).test_client()
    return cliente.post("/validar", data={"cpf": "x"}).get_data(as_text=True)


def test_pagina_tem_icone_vazio_para_nao_gerar_404_de_favicon():
    html = create_app().test_client().get("/").get_data(as_text=True)
    assert 'rel="icon"' in html


def test_decisao_usa_role_status_para_leitores_de_tela():
    html = _html_do_resultado(Resultado("52998224725", Desfecho.APROVADO, "ok"))
    assert 'role="status"' in html


def test_falha_tecnica_usa_role_alert():
    def falha(cpf):
        raise ConfigError("faltou config")

    html = create_app(falha).test_client().post("/validar", data={"cpf": "x"}).get_data(as_text=True)
    assert 'role="alert"' in html


@pytest.mark.parametrize("status", ["APROVADO", "REPROVADO", "INVALIDO", "INDISPONIVEL"])
def test_cada_status_tem_estilo_proprio(status):
    # Se alguém renomear um status e esquecer o CSS, este teste avisa.
    html = create_app().test_client().get("/").get_data(as_text=True)
    assert f'#resultado[data-status="{status}"]' in html


def test_resultado_tem_o_link_de_nova_consulta():
    html = _html_do_resultado(Resultado("52998224725", Desfecho.APROVADO, "ok"))
    assert 'id="link-nova-consulta"' in html