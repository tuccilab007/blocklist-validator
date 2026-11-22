"""Preparação compartilhada dos testes.

Os testes de integração usam o PostgreSQL de verdade (com o seed aplicado).
Se o banco estiver fora do ar ou sem o seed, eles são PULADOS em vez de falhar.
"""
import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from blocklist import config, db


@pytest.fixture(scope="session")
def engine_real():
    try:
        engine = db.get_engine()
        with engine.connect() as conexao:
            total = conexao.execute(text("SELECT COUNT(*) FROM blocklist")).scalar_one()
    except (SQLAlchemyError, config.ConfigError) as erro:
        pytest.skip(f"Banco indisponível: {erro}")
    if total == 0:
        pytest.skip("Seed não aplicado: rode python -m blocklist.sql_runner sql\\02_seed.sql")
    return engine