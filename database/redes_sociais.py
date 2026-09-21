from database.connection import get_connection

# BUSCAR REDES SOCIAIS DO ESTABELECIMENTO

def buscar_por_estabelecimento(estabelecimento_id):

    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)

    try:

        query = """
            SELECT
                id,
                estabelecimento_id,
                plataforma,
                url,
                ativo
            FROM redes_sociais
            WHERE estabelecimento_id = %s
            ORDER BY id ASC
        """

        cursor.execute(
            query,
            (estabelecimento_id,)
        )

        return cursor.fetchall()

    finally:

        cursor.close()
        conexao.close()



def buscar_por_id(
    rede_id,
    estabelecimento_id
):

    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)

    try:

        query = """
            SELECT
                id,
                estabelecimento_id,
                plataforma,
                url,
                ativo
            FROM redes_sociais
            WHERE id = %s
              AND estabelecimento_id = %s
        """

        cursor.execute(
            query,
            (
                rede_id,
                estabelecimento_id
            )
        )

        return cursor.fetchone()

    finally:

        cursor.close()
        conexao.close()



def criar(
    estabelecimento_id,
    plataforma,
    url
):

    conexao = get_connection()
    cursor = conexao.cursor()

    try:

        query = """
            INSERT INTO redes_sociais (
                estabelecimento_id,
                plataforma,
                url
            )
            VALUES (
                %s,
                %s,
                %s
            )
        """

        cursor.execute(
            query,
            (
                estabelecimento_id,
                plataforma,
                url
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



def atualizar(
    rede_id,
    estabelecimento_id,
    plataforma,
    url
):

    conexao = get_connection()
    cursor = conexao.cursor()

    try:

        query = """
            UPDATE redes_sociais
            SET
                plataforma = %s,
                url = %s
            WHERE id = %s
              AND estabelecimento_id = %s
        """

        cursor.execute(
            query,
            (
                plataforma,
                url,
                rede_id,
                estabelecimento_id
            )
        )

        conexao.commit()

    except Exception:

        conexao.rollback()
        raise

    finally:

        cursor.close()
        conexao.close()


def excluir(
    rede_id,
    estabelecimento_id
):

    conexao = get_connection()
    cursor = conexao.cursor()

    try:

        query = """
            DELETE FROM redes_sociais
            WHERE id = %s
              AND estabelecimento_id = %s
        """

        cursor.execute(
            query,
            (
                rede_id,
                estabelecimento_id
            )
        )

        conexao.commit()

    except Exception:

        conexao.rollback()
        raise

    finally:

        cursor.close()
        conexao.close()


# ==========================================================
# ALTERAR STATUS
# ==========================================================

def alterar_status(
    rede_id,
    estabelecimento_id,
    ativo
):

    conexao = get_connection()
    cursor = conexao.cursor()

    try:

        query = """
            UPDATE redes_sociais
            SET ativo = %s
            WHERE id = %s
              AND estabelecimento_id = %s
        """

        cursor.execute(
            query,
            (
                ativo,
                rede_id,
                estabelecimento_id
            )
        )

        conexao.commit()

    except Exception:

        conexao.rollback()
        raise

    finally:

        cursor.close()
        conexao.close()
