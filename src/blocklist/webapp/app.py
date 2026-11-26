"""Aplicação web: o formulário fictício que simula o validador de blocklist.

Como subir o servidor de desenvolvimento (com o .venv ativo, na raiz):
    python -m flask --app blocklist.webapp.app:create_app run --debug

Depois abra http://127.0.0.1:5000 no navegador.

Atenção: este servidor é só para desenvolvimento. Em produção seria preciso
um servidor WSGI de verdade, HTTPS, autenticação e proteção CSRF.
"""
from flask import Flask, jsonify, render_template, request
from sqlalchemy.exc import SQLAlchemyError

from blocklist.config import ConfigError
from blocklist.cpf import formatar_cpf
from blocklist.logger import get_logger
from blocklist.porteiro import validar_candidato

log = get_logger(__name__)

# Só para não processar textos gigantes enviados por engano (ou de propósito).
TAMANHO_MAXIMO_CPF = 30


def _pagina_indisponivel(cpf_digitado: str):
    """Resposta HTTP 503: não deu para consultar, então NÃO há decisão."""
    html = render_template(
        "resultado.html", indisponivel=True, cpf_exibicao=cpf_digitado
    )
    return html, 503


def create_app(validador=validar_candidato) -> Flask:
    """Fábrica da aplicação: cada chamada devolve uma app nova e independente.

    O `validador` é quem decide (o porteiro). Nos testes passamos um falso,
    sem banco.
    """
    app = Flask(__name__)  # procura a pasta "templates" ao lado deste arquivo

    @app.get("/")
    def formulario():
        """Mostra o formulário para digitar o CPF."""
        return render_template("form.html")

    @app.post("/validar")
    def validar():
        """Recebe o CPF do formulário, pergunta ao porteiro e mostra a decisão."""
        cpf_digitado = request.form.get("cpf", "")[:TAMANHO_MAXIMO_CPF]
        try:
            resultado = validador(cpf_digitado)
        except ConfigError as erro:
            log.error("Configuração incompleta: %s", erro)
            return _pagina_indisponivel(cpf_digitado)
        except SQLAlchemyError as erro:
            # str(erro) do SQLAlchemy traz o SQL e os parâmetros (o CPF!).
            # Por isso registramos só a mensagem do driver do banco.
            log.error(
                "Falha ao consultar o banco: %s",
                getattr(erro, "orig", type(erro).__name__),
            )
            return _pagina_indisponivel(cpf_digitado)

        # Decisões de negócio (aprovado, reprovado, inválido) são HTTP 200.
        # Só falha técnica vira erro HTTP.
        cpf_exibicao = (
            formatar_cpf(resultado.cpf) if len(resultado.cpf) == 11 else cpf_digitado
        )
        return render_template(
            "resultado.html", resultado=resultado, cpf_exibicao=cpf_exibicao
        )

    @app.get("/saude")
    def saude():
        """Rota de 'está vivo?'. Útil para testar e, depois, para o robô conferir."""
        return jsonify(status="ok")

    log.info("Aplicação web criada")
    return app