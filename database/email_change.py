import secrets
from datetime import datetime, timedelta

from database.connection import get_connection


def criar_token(usuario_id, novo_email, validade_minutos=60):
    token = secrets.token_urlsafe(32)
    expira_em = datetime.now() + timedelta(minutes=validade_minutos)
    conexao = get_connection()
    cursor = conexao.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO email_change_tokens (usuario_id, novo_email, token, expira_em)
            VALUES (%s, %s, %s, %s)
            """,
            (usuario_id, novo_email, token, expira_em)
        )
        conexao.commit()
        return token
    except Exception:
        conexao.rollback()
        raise
    finally:
        cursor.close()
        conexao.close()


def buscar_token(token):
    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, usuario_id, novo_email, token, expira_em, usado
            FROM email_change_tokens
            WHERE token = %s
            LIMIT 1
            """,
            (token,)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conexao.close()


def invalidar_tokens_usuario(usuario_id):
    conexao = get_connection()
    cursor = conexao.cursor()

    try:
        cursor.execute(
            """
            UPDATE email_change_tokens
            SET usado = 1
            WHERE usuario_id = %s AND usado = 0
            """,
            (usuario_id,)
        )
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        cursor.close()
        conexao.close()

def marcar_como_usado(token):
    conexao = get_connection()
    cursor = conexao.cursor()

    try:
        cursor.execute(
            """
            UPDATE email_change_tokens
            SET usado = 1
            WHERE token = %s
              AND usado = 0
              AND expira_em >= %s
            """,
            (
                token,
                datetime.now()
            )
        )

        conexao.commit()

        return cursor.rowcount == 1

    except Exception:
        conexao.rollback()
        raise

    finally:
        cursor.close()
        conexao.close()
