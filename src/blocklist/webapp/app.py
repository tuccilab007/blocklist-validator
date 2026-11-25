"""Aplicação web: o formulário fictício que simula o validador de blocklist.

Como subir o servidor de desenvolvimento (com o .venv ativo, na raiz):
    python -m flask --app blocklist.webapp.app:create_app run --debug

Depois abra http://127.0.0.1:5000 no navegador.
"""
from flask import Flask, jsonify, render_template

from blocklist.logger import get_logger

log = get_logger(__name__)


def create_app() -> Flask:
    """Fábrica da aplicação: cada chamada devolve uma app nova e independente.

    Ter uma fábrica (em vez de uma app global) facilita os testes, que podem
    criar quantas apps quiserem sem uma interferir na outra.
    """
    app = Flask(__name__)  # procura a pasta "templates" ao lado deste arquivo

    @app.get("/")
    def formulario():
        """Mostra o formulário para digitar o CPF."""
        return render_template("form.html")

    @app.get("/saude")
    def saude():
        """Rota de 'está vivo?'. Útil para testar e, depois, para o robô conferir."""
        return jsonify(status="ok")

    log.info("Aplicação web criada")
    return app