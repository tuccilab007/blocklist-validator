from datetime import date

from blocklist.repositorio import buscar_bloqueio, buscar_passagem_mais_recente

# Estes testes dependem do seed (sql/02_seed.sql) e rodam no PostgreSQL real.


def test_cpf_na_blocklist_devolve_motivo_e_data(engine_real):
    bloqueio = buscar_bloqueio("52998224725", engine_real)
    assert bloqueio is not None
    assert bloqueio.motivo == "Mau comportamento"
    assert bloqueio.bloqueado_em == date(2024, 3, 12)


def test_cpf_fora_da_blocklist_devolve_none(engine_real):
    assert buscar_bloqueio("16180339805", engine_real) is None


def test_texto_malicioso_nao_quebra_nem_acha_nada(engine_real):
    # Se o SQL fosse montado com f-string, isto devolveria alguém.
    assert buscar_bloqueio("' OR '1'='1", engine_real) is None


def test_passagem_mais_recente_ignora_a_antiga(engine_real):
    # Fernando Rocha tem duas passagens: 2020 (curta) e 2021 a 2025 (longa)
    passagem = buscar_passagem_mais_recente("98765432100", engine_real)
    assert passagem is not None
    assert passagem.data_admissao == date(2021, 5, 10)
    assert passagem.data_desligamento == date(2025, 11, 28)


def test_funcionario_ativo_tem_desligamento_vazio(engine_real):
    passagem = buscar_passagem_mais_recente("16180339805", engine_real)
    assert passagem is not None
    assert passagem.data_desligamento is None


def test_cpf_que_nunca_trabalhou_devolve_none(engine_real):
    assert buscar_passagem_mais_recente("11235813207", engine_real) is None