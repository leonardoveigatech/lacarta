from database.connection import get_connection
from werkzeug.security import check_password_hash, generate_password_hash


def buscar_por_email(email):
    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)

    query = """
        SELECT
            id,
            estabelecimento_id,
            nome,
            email,
            email_confirmado,
            senha,
            senha_alterada_em,
            ativo
        FROM usuarios
        WHERE email = %s
        LIMIT 1
    """

    try:
        cursor.execute(query, (email,))
        return cursor.fetchone()

    finally:
        cursor.close()
        conexao.close()


def buscar_por_id(usuario_id):
    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)

    query = """
        SELECT
            id,
            estabelecimento_id,
            nome,
            email,
            email_confirmado,
            senha,
            senha_alterada_em,
            ativo
        FROM usuarios
        WHERE id = %s
        LIMIT 1
    """

    try:
        cursor.execute(query, (usuario_id,))
        return cursor.fetchone()

    finally:
        cursor.close()
        conexao.close()


def verificar_senha(senha_digitada, senha_hash):
    return check_password_hash(
        senha_hash,
        senha_digitada
    )


def criar_usuario(
    estabelecimento_id,
    nome,
    email,
    senha
):
    conexao = get_connection()
    cursor = conexao.cursor()

    senha_hash = generate_password_hash(senha)

    query = """
        INSERT INTO usuarios (
            estabelecimento_id,
            nome,
            email,
            senha
        )
        VALUES (%s, %s, %s, %s)
    """

    try:
        cursor.execute(
            query,
            (
                estabelecimento_id,
                nome,
                email,
                senha_hash
            )
        )

        conexao.commit()

        return cursor.lastrowid

    except Exception:
        conexao.rollback()
        raise

    finally:
        cursor.close()
        conexao.close()


def atualizar_dados(usuario_id, nome, email):
    conexao = get_connection()
    cursor = conexao.cursor()

    query = """
        UPDATE usuarios
        SET
            nome = %s,
            email = %s
        WHERE id = %s
    """

    try:
        cursor.execute(
            query,
            (
                nome,
                email,
                usuario_id
            )
        )

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        cursor.close()
        conexao.close()


def atualizar_senha(usuario_id, senha):
    conexao = get_connection()
    cursor = conexao.cursor()

    senha_hash = generate_password_hash(senha)

    query = """
        UPDATE usuarios
        SET
            senha = %s,
            senha_alterada_em = CURRENT_TIMESTAMP
        WHERE id = %s
    """

    try:
        cursor.execute(
            query,
            (
                senha_hash,
                usuario_id
            )
        )

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        cursor.close()
        conexao.close()


def atualizar_nome(usuario_id, nome):
    conexao = get_connection()
    cursor = conexao.cursor()

    try:
        cursor.execute(
            "UPDATE usuarios SET nome = %s WHERE id = %s",
            (nome, usuario_id)
        )

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        cursor.close()
        conexao.close()


def atualizar_email(usuario_id, email):
    conexao = get_connection()
    cursor = conexao.cursor()

    try:
        cursor.execute(
            "UPDATE usuarios SET email = %s WHERE id = %s",
            (email, usuario_id)
        )

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        cursor.close()
        conexao.close()