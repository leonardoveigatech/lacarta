from database.connection import get_connection


# ==========================================================
# BUSCAR APARÊNCIA
# ==========================================================

def buscar_por_estabelecimento(estabelecimento_id):

    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)

    try:

        query = """
            SELECT
                id,
                estabelecimento_id,

                cor_principal,
                cor_secundaria,
                cor_texto,

                fonte_titulo,
                fonte_texto,
                layout_produtos,
                tamanho_imagem,
                mostrar_descricao,
                mostrar_localizacao,
                mostrar_horarios,
                mostrar_whatsapp,
                mostrar_redes_sociais

            FROM aparencias

            WHERE estabelecimento_id = %s

            LIMIT 1
        """

        cursor.execute(
            query,
            (estabelecimento_id,)
        )

        return cursor.fetchone()

    finally:

        cursor.close()
        conexao.close()


# ==========================================================
# CRIAR APARÊNCIA
# ==========================================================

def criar(
    estabelecimento_id,
    cor_principal,
    cor_secundaria,
    cor_texto,
    fonte_titulo,
    fonte_texto,
    layout_produtos,
    tamanho_imagem,
    mostrar_descricao,
    mostrar_localizacao,
    mostrar_horarios,
    mostrar_whatsapp,
    mostrar_redes_sociais
):

    conexao = get_connection()
    cursor = conexao.cursor()

    try:

        query = """
            INSERT INTO aparencias (
                estabelecimento_id,

                cor_principal,
                cor_secundaria,
                cor_texto,

                fonte_titulo,
                fonte_texto,
                layout_produtos,
                tamanho_imagem,
                mostrar_descricao,
                mostrar_localizacao,
                mostrar_horarios,
                mostrar_whatsapp,
                mostrar_redes_sociais
            )

            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """

        valores = (
            estabelecimento_id,

            cor_principal,
            cor_secundaria,
            cor_texto,

            fonte_titulo,
            fonte_texto,
            layout_produtos,
            tamanho_imagem,
            mostrar_descricao,
            mostrar_localizacao,
            mostrar_horarios,
            mostrar_whatsapp,
            mostrar_redes_sociais
        )

        cursor.execute(query, valores)

        conexao.commit()

        return cursor.lastrowid

    except Exception:

        conexao.rollback()
        raise

    finally:

        cursor.close()
        conexao.close()


# ==========================================================
# ATUALIZAR APARÊNCIA
# ==========================================================

def atualizar(
    estabelecimento_id,
    cor_principal,
    cor_secundaria,
    cor_texto,
    fonte_titulo,
    fonte_texto,
    layout_produtos,
    tamanho_imagem,
    mostrar_descricao,
    mostrar_localizacao,
    mostrar_horarios,
    mostrar_whatsapp,
    mostrar_redes_sociais
):

    conexao = get_connection()
    cursor = conexao.cursor()

    try:

        query = """
            UPDATE aparencias

            SET
                cor_principal = %s,
                cor_secundaria = %s,
                cor_texto = %s,

                fonte_titulo = %s,
                fonte_texto = %s,
                layout_produtos = %s,
                tamanho_imagem = %s,
                mostrar_descricao = %s,
                mostrar_localizacao = %s,
                mostrar_horarios = %s,
                mostrar_whatsapp = %s,
                mostrar_redes_sociais = %s

            WHERE estabelecimento_id = %s
        """

        valores = (
            cor_principal,
            cor_secundaria,
            cor_texto,

            fonte_titulo,
            fonte_texto,
            layout_produtos,
            tamanho_imagem,
            mostrar_descricao,
            mostrar_localizacao,
            mostrar_horarios,
            mostrar_whatsapp,
            mostrar_redes_sociais,

            estabelecimento_id
        )

        cursor.execute(query, valores)

        conexao.commit()

    except Exception:

        conexao.rollback()
        raise

    finally:

        cursor.close()
        conexao.close()