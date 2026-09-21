import secrets

from flask import session, abort


def gerar_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)

    return session["csrf_token"]


def validar_csrf_token(token):
    token_session = session.get("csrf_token")

    if not token_session or not token:
        abort(403)

    if not secrets.compare_digest(
        token_session,
        token
    ):
        abort(403)