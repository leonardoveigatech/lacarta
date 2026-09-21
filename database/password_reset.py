import secrets
from datetime import datetime, timedelta

from database.connection import get_connection


def criar_token(usuario_id, validade_minutos=60):
    token = secrets.token_urlsafe(32)

    expira_em = datetime.now() + timedelta(
        minutes=validade_minutos
    )

    conexao = get_connection()
    cursor = conexao.cursor()

    query = """
        INSERT INTO password_reset_tokens (
            usuario_id,
            token,
            expira_em
        )
        VALUES (%s, %s, %s)
    """

    try:
        cursor.execute(
            query,
            (
                usuario_id,
                token,
                expira_em
            )
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

    query = """
        SELECT
            id,
            usuario_id,
            token,
            expira_em,
            usado,
            criado_em
        FROM password_reset_tokens
        WHERE token = %s
        LIMIT 1
    """

    try:
        cursor.execute(query, (token,))
        return cursor.fetchone()

    finally:
        cursor.close()
        conexao.close()


def marcar_como_usado(token):
    conexao = get_connection()
    cursor = conexao.cursor()

    query = """
        UPDATE password_reset_tokens
        SET usado = 1
        WHERE token = %s
          AND usado = 0
          AND expira_em >= NOW()
    """

    try:
        cursor.execute(
            query,
            (token,)
        )

        conexao.commit()

        return cursor.rowcount == 1

    except Exception:
        conexao.rollback()
        raise

    finally:
        cursor.close()
        conexao.close()

def invalidar_tokens_usuario(usuario_id):
    conexao = get_connection()
    cursor = conexao.cursor()

    query = """
        UPDATE password_reset_tokens
        SET usado = 1
        WHERE usuario_id = %s
          AND usado = 0
    """

    try:
        cursor.execute(query, (usuario_id,))
        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        cursor.close()
        conexao.close()