from database.connection import get_connection



def buscar_por_categoria(
    categoria_id,
    estabelecimento_id
):
    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)

    try:
        query = """
            SELECT
                id,
                estabelecimento_id,
                categoria_id,
                nome,
                ordem,
                ativo,
                disponivel
            FROM subcategorias
            WHERE categoria_id = %s
              AND estabelecimento_id = %s
            ORDER BY ordem ASC, id ASC
        """

        cursor.execute(
            query,
            (
                categoria_id,
                estabelecimento_id
            )
        )

        return cursor.fetchall()

    finally:
        cursor.close()
        conexao.close()



def buscar_por_id(
    subcategoria_id,
    estabelecimento_id
):
    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)

    try:
        query = """
            SELECT
                id,
                estabelecimento_id,
                categoria_id,
                nome,
                ordem,
                ativo,
                disponivel
            FROM subcategorias
            WHERE id = %s
              AND estabelecimento_id = %s
        """

        cursor.execute(
            query,
            (
                subcategoria_id,
                estabelecimento_id
            )
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        conexao.close()


def criar_subcategoria(
    estabelecimento_id,
    categoria_id,
    nome,
    ordem
):
    conexao = get_connection()
    cursor = conexao.cursor()

    try:
        query = """
            INSERT INTO subcategorias (
                estabelecimento_id,
                categoria_id,
                nome,
                ordem,
                ativo,
                disponivel
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                1,
                1
            )
        """

        cursor.execute(
            query,
            (
                estabelecimento_id,
                categoria_id,
                nome,
                ordem
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



def atualizar_subcategoria(
    subcategoria_id,
    estabelecimento_id,
    nome,
    ordem
):
    conexao = get_connection()
    cursor = conexao.cursor()

    try:
        query = """
            UPDATE subcategorias
            SET
                nome = %s,
                ordem = %s
            WHERE id = %s
              AND estabelecimento_id = %s
        """

        cursor.execute(
            query,
            (
                nome,
                ordem,
                subcategoria_id,
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



def alterar_disponibilidade(
    subcategoria_id,
    estabelecimento_id,
    disponivel
):
    conexao = get_connection()
    cursor = conexao.cursor()

    try:
        query = """
            UPDATE subcategorias
            SET
                disponivel = %s
            WHERE id = %s
              AND estabelecimento_id = %s
        """

        cursor.execute(
            query,
            (
                disponivel,
                subcategoria_id,
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



def excluir_subcategoria(
    subcategoria_id,
    estabelecimento_id
):
    conexao = get_connection()
    cursor = conexao.cursor()

    try:
        query = """
            DELETE FROM subcategorias
            WHERE id = %s
              AND estabelecimento_id = %s
        """

        cursor.execute(
            query,
            (
                subcategoria_id,
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
