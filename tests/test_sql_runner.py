from blocklist import config
from blocklist.sql_runner import dividir_comandos


def test_dividir_comandos_ignora_comentarios_e_espacos():
    script = """
    -- comentário; com ponto e vírgula
    CREATE TABLE a (id INTEGER);

    -- outro comentário
    CREATE TABLE b (id INTEGER);
    """
    assert dividir_comandos(script) == [
        "CREATE TABLE a (id INTEGER)",
        "CREATE TABLE b (id INTEGER)",
    ]


def test_dividir_comandos_sem_ponto_e_virgula_final():
    assert dividir_comandos("SELECT 1") == ["SELECT 1"]


def test_dividir_comandos_script_vazio():
    assert dividir_comandos("-- só comentário\n\n") == []


def test_schema_tem_duas_tabelas():
    texto = (config.DIR_SQL / "01_schema.sql").read_text(encoding="utf-8")
    comandos = dividir_comandos(texto)
    assert len(comandos) == 2
    assert all(c.startswith("CREATE TABLE IF NOT EXISTS") for c in comandos)
    assert "blocklist" in comandos[0]
    assert "funcionarios" in comandos[1]