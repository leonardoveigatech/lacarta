from datetime import timedelta

from flask import Flask, request, render_template

from config import (
    SECRET_KEY,
    SESSION_COOKIE_SECURE,
    SESSION_COOKIE_SAMESITE,
    SESSION_LIFETIME_MINUTES,
    MAX_UPLOAD_BYTES
)
from utils.csrf import gerar_csrf_token, validar_csrf_token

from routes.public import public
from routes.admin import admin
from routes.auth import auth


app = Flask(__name__)

app.secret_key = SECRET_KEY
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=SESSION_COOKIE_SECURE,
    SESSION_COOKIE_SAMESITE=SESSION_COOKIE_SAMESITE,
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=SESSION_LIFETIME_MINUTES),
    SESSION_REFRESH_EACH_REQUEST=True,
    MAX_CONTENT_LENGTH=MAX_UPLOAD_BYTES,
)

app.jinja_env.globals["csrf_token"] = gerar_csrf_token


@app.before_request
def proteger_requisicoes_de_alteracao():
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        validar_csrf_token(
            request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
        )

@app.after_request
def adicionar_headers_seguranca(resposta):
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    resposta.headers["X-Frame-Options"] = "SAMEORIGIN"
    resposta.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resposta.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return resposta



@app.errorhandler(404)
def pagina_nao_encontrada(erro):
    return render_template("404.html"), 404


@app.errorhandler(500)
def erro_interno(erro):
    app.logger.exception("Erro interno no servidor")
    return render_template("500.html"), 500

app.register_blueprint(auth)
app.register_blueprint(public)
app.register_blueprint(admin)


if __name__ == "__main__":
    print("DEBUG LA CARTA ATIVO")
    app.run(debug=True, use_reloader=False)
