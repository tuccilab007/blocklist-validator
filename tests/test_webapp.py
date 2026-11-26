import pytest
from sqlalchemy.exc import OperationalError

from blocklist.config import ConfigError
from blocklist.porteiro import Desfecho, Resultado
from blocklist.webapp.app import create_app

APROVADO = Resultado("52998224725", Desfecho.APROVADO, "Nenhuma restrição encontrada")


def _cliente(validador=None):
    app = create_app(validador) if validador else create_app()
    return app.test_client()


def _validador_fixo(resultado, chamadas=None):
    def validador(cpf):
        if chamadas is not None:
            chamadas.append(cpf)
        return resultado

    return validador


def _validador_que_falha(erro):
    def validador(cpf):
        raise erro

    return validador


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


def test_validar_so_aceita_post():
    assert _cliente().get("/validar").status_code == 405


def test_validar_mostra_a_decisao_do_porteiro():
    resposta = _cliente(_validador_fixo(APROVADO)).post(
        "/validar", data={"cpf": "529.982.247-25"}
    )
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert 'id="resultado"' in html
    assert 'data-status="APROVADO"' in html
    assert 'data-desfecho="APROVADO"' in html
    assert "Nenhuma restrição encontrada" in html
    assert "529.982.247-25" in html  # CPF mostrado formatado


def test_reprovacao_tambem_e_http_200_e_traz_o_desfecho():
    reprovado = Resultado(
        "52998224725", Desfecho.BLOQUEIO_EMPRESA, "Bloqueado pela empresa"
    )
    resposta = _cliente(_validador_fixo(reprovado)).post("/validar", data={"cpf": "x"})
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert 'data-status="REPROVADO"' in html
    assert 'data-desfecho="BLOQUEIO_EMPRESA"' in html


def test_validar_repassa_o_texto_digitado_ao_porteiro():
    chamadas = []
    _cliente(_validador_fixo(APROVADO, chamadas)).post(
        "/validar", data={"cpf": "529.982.247-25"}
    )
    assert chamadas == ["529.982.247-25"]


def test_validar_sem_o_campo_cpf_manda_texto_vazio():
    chamadas = []
    _cliente(_validador_fixo(APROVADO, chamadas)).post("/validar", data={})
    assert chamadas == [""]


def test_texto_gigante_e_cortado_antes_de_chegar_ao_porteiro():
    chamadas = []
    _cliente(_validador_fixo(APROVADO, chamadas)).post(
        "/validar", data={"cpf": "9" * 5000}
    )
    assert len(chamadas[0]) == 30


def test_motivo_com_html_e_escapado_na_pagina():
    perigoso = Resultado(
        "52998224725", Desfecho.BLOQUEIO_EMPRESA, "<script>alert(1)</script>"
    )
    html = (
        _cliente(_validador_fixo(perigoso))
        .post("/validar", data={"cpf": "x"})
        .get_data(as_text=True)
    )
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


@pytest.mark.parametrize(
    "erro",
    [
        OperationalError("SELECT 1", {"cpf": "52998224725"}, Exception("conexão recusada")),
        ConfigError("Variável DB_USER ausente ou vazia"),
    ],
)
def test_falha_do_banco_vira_503_sem_decisao(erro):
    resposta = _cliente(_validador_que_falha(erro)).post(
        "/validar", data={"cpf": "529.982.247-25"}
    )
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 503
    assert 'data-status="INDISPONIVEL"' in html
    assert "APROVADO" not in html
    assert "REPROVADO" not in html


# Elenco do seed no PostgreSQL real, passando pelo formulário de verdade.
@pytest.mark.parametrize(
    "cpf, status, desfecho",
    [
        ("529.982.247-25", "REPROVADO", "BLOQUEIO_EMPRESA"),
        ("135.792.468-28", "REPROVADO", "EX_FUNCIONARIO_RECENTE"),
        ("314.159.265-90", "APROVADO", "APROVADO"),
        ("111.111.111-11", "INVALIDO", "CPF_INVALIDO"),
    ],
)
def test_formulario_com_banco_real(engine_real, cpf, status, desfecho):
    resposta = _cliente().post("/validar", data={"cpf": cpf})
    html = resposta.get_data(as_text=True)
    assert resposta.status_code == 200
    assert f'data-status="{status}"' in html
    assert f'data-desfecho="{desfecho}"' in html