import logging

from blocklist import config, logger


def test_configurar_logs_duas_vezes_nao_duplica_handlers():
    logger.configurar_logs()
    quantidade = len(logging.getLogger().handlers)
    logger.configurar_logs()
    assert len(logging.getLogger().handlers) == quantidade


def test_mensagem_vai_para_o_arquivo_de_log():
    log = logger.get_logger("teste")
    log.warning("mensagem de teste do logger")
    for handler in logging.getLogger().handlers:
        handler.flush()
    conteudo = (config.DIR_LOGS / "blocklist.log").read_text(encoding="utf-8")
    assert "mensagem de teste do logger" in conteudo