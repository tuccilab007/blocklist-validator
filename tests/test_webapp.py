from blocklist.webapp.app import create_app


def _cliente():
    return create_app().test_client()


def test_saude_responde_ok():
    resposta = _cliente().get("/saude")
    assert resposta.status_code == 200
    assert resposta.get_json() == {"status": "ok"}


def test_rota_inexistente_da_404():
    assert _cliente().get("/nao-existe").status_code == 404


def test_formulario_abre_com_a_pagina_html():
    resposta = _cliente().get("/")
    assert resposta.status_code == 200
    assert "text/html" in resposta.content_type
    assert "Validador de Blocklist" in resposta.get_data(as_text=True)


def test_formulario_tem_os_ids_que_o_robo_vai_usar():
    # Contrato com o robô (Capítulo 6): se mudar um id, o robô quebra.
    html = _cliente().get("/").get_data(as_text=True)
    assert 'id="form-validacao"' in html
    assert 'id="cpf"' in html
    assert 'name="cpf"' in html
    assert 'id="btn-validar"' in html
    assert 'method="post"' in html