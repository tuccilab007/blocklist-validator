"""Configurações do projeto.

Tudo que muda de máquina para máquina (host, usuário, senha, URL) vem do
arquivo .env. Nada sensível fica escrito no código.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Raiz do projeto: src/blocklist/config.py -> sobe 2 níveis (blocklist, src)
RAIZ_PROJETO = Path(__file__).resolve().parents[2]
DIR_ENTRADA = RAIZ_PROJETO / "data" / "input"
DIR_SAIDA = RAIZ_PROJETO / "data" / "output"
DIR_LOGS = RAIZ_PROJETO / "logs"
DIR_SQL = RAIZ_PROJETO / "sql"

NIVEIS_LOG = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

# Lê o .env da raiz. Se a variável já existir no sistema, ela tem prioridade.
load_dotenv(RAIZ_PROJETO / ".env")


class ConfigError(Exception):
    """Configuração ausente ou inválida."""


@dataclass(frozen=True)
class Banco:
    """Dados de conexão com o PostgreSQL."""

    host: str
    porta: int
    nome: str
    usuario: str
    senha: str = field(repr=False)  # repr=False: a senha nunca aparece em print/log


def _obrigatoria(nome: str) -> str:
    valor = os.getenv(nome, "").strip()
    if not valor:
        raise ConfigError(
            f"Variável {nome} ausente ou vazia. Preencha no arquivo .env"
        )
    return valor


def carregar_banco() -> Banco:
    """Monta a configuração do banco a partir do ambiente (.env)."""
    texto_porta = os.getenv("DB_PORT", "5432").strip()
    try:
        porta = int(texto_porta)
    except ValueError as erro:
        raise ConfigError(
            f"DB_PORT inválida: {texto_porta!r} (use apenas números)"
        ) from erro
    return Banco(
        host=os.getenv("DB_HOST", "localhost").strip(),
        porta=porta,
        nome=_obrigatoria("DB_NAME"),
        usuario=_obrigatoria("DB_USER"),
        senha=_obrigatoria("DB_PASSWORD"),
    )


def url_app() -> str:
    """Endereço do formulário web que o robô vai preencher."""
    return os.getenv("APP_URL", "http://127.0.0.1:5000").strip()


def nivel_log() -> str:
    """Nível de log (DEBUG, INFO, WARNING, ERROR ou CRITICAL)."""
    nivel = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    if nivel not in NIVEIS_LOG:
        raise ConfigError(
            f"LOG_LEVEL inválido: {nivel!r}. Use um de: {sorted(NIVEIS_LOG)}"
        )
    return nivel