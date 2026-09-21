from database.connection import get_connection


def buscar_por_estabelecimento(estabelecimento_id):

    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)

    try:

        query = """
            SELECT
                id,
                estabelecimento_id,
                categoria_id,
                subcategoria_id,
                nome,
                descricao,
                preco,
                imagem,
                disponivel,
                ordem,
                informacoes_adicionais
            FROM produtos
            WHERE estabelecimento_id = %s
              AND disponivel = 1
            ORDER BY ordem ASC, id ASC
        """

        cursor.execute(
            query,
            (estabelecimento_id,)
        )

        return cursor.fetchall()

    finally:

        cursor.close()
        conexao.close()


def buscar_todos_por_estabelecimento(estabelecimento_id):

    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)

    try:

        query = """
            SELECT
                id,
                estabelecimento_id,
                categoria_id,
                subcategoria_id,
                nome,
                descricao,
                preco,
                imagem,
                disponivel,
                ordem,
                informacoes_adicionais
            FROM produtos
            WHERE estabelecimento_id = %s
            ORDER BY ordem ASC, id ASC
        """

        cursor.execute(
            query,
            (estabelecimento_id,)
        )

        return cursor.fetchall()

    finally:

        cursor.close()
        conexao.close()


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
                subcategoria_id,
                nome,
                descricao,
                preco,
                imagem,
                disponivel,
                ordem,
                informacoes_adicionais
            FROM produtos
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



def buscar_por_subcategoria(
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
                subcategoria_id,
                nome,
                descricao,
                preco,
                imagem,
                disponivel,
                ordem,
                informacoes_adicionais
            FROM produtos
            WHERE subcategoria_id = %s
              AND estabelecimento_id = %s
            ORDER BY ordem ASC, id ASC
        """

        cursor.execute(
            query,
            (
                subcategoria_id,
                estabelecimento_id
            )
        )

        return cursor.fetchall()

    finally:

        cursor.close()
        conexao.close()



def buscar_por_id(
    produto_id,
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
                subcategoria_id,
                nome,
                descricao,
                preco,
                imagem,
                disponivel,
                ordem,
                informacoes_adicionais
            FROM produtos
            WHERE id = %s
              AND estabelecimento_id = %s
        """

        cursor.execute(
            query,
            (
                produto_id,
                estabelecimento_id
            )
        )

        return cursor.fetchone()

    finally:

        cursor.close()
        conexao.close()

def buscar_por_termo(
    estabelecimento_id,
    termo
):

    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)

    try:

        query = """
            SELECT
                p.id,
                p.estabelecimento_id,
                p.categoria_id,
                p.subcategoria_id,
                p.nome,
                p.descricao,
                p.preco,
                p.imagem,
                p.disponivel,
                p.ordem,
                p.informacoes_adicionais
            FROM produtos p
            INNER JOIN categorias c
                ON c.id = p.categoria_id
               AND c.estabelecimento_id = p.estabelecimento_id
            LEFT JOIN subcategorias s
                ON s.id = p.subcategoria_id
               AND s.estabelecimento_id = p.estabelecimento_id
            WHERE p.estabelecimento_id = %s
              AND p.disponivel = 1
              AND c.ativo = 1
              AND (
                  p.subcategoria_id IS NULL
                  OR s.disponivel = 1
              )
              AND (
                  p.nome LIKE %s
                  OR p.descricao LIKE %s
              )
            ORDER BY p.nome ASC
        """

        termo_busca = f"%{termo}%"

        cursor.execute(
            query,
            (
                estabelecimento_id,
                termo_busca,
                termo_busca
            )
        )

        return cursor.fetchall()

    finally:

        cursor.close()
        conexao.close()


def criar_produto(
    estabelecimento_id,
    categoria_id,
    subcategoria_id,
    nome,
    descricao,
    preco,
    imagem,
    disponivel,
    ordem,
    informacoes_adicionais
):

    conexao = get_connection()
    cursor = conexao.cursor()

    try:

        query = """
            INSERT INTO produtos (
                estabelecimento_id,
                categoria_id,
                subcategoria_id,
                nome,
                descricao,
                preco,
                imagem,
                disponivel,
                ordem,
                informacoes_adicionais
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
                %s
            )
        """

        cursor.execute(
            query,
            (
                estabelecimento_id,
                categoria_id,
                subcategoria_id,
                nome,
                descricao,
                preco,
                imagem,
                disponivel,
                ordem,
                informacoes_adicionais
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


def atualizar_produto(
    produto_id,
    estabelecimento_id,
    categoria_id,
    subcategoria_id,
    nome,
    descricao,
    preco,
    imagem,
    disponivel,
    ordem,
    informacoes_adicionais
):

    conexao = get_connection()
    cursor = conexao.cursor()

    try:

        query = """
            UPDATE produtos
            SET
                categoria_id = %s,
                subcategoria_id = %s,
                nome = %s,
                descricao = %s,
                preco = %s,
                imagem = %s,
                disponivel = %s,
                ordem = %s,
                informacoes_adicionais = %s
            WHERE id = %s
              AND estabelecimento_id = %s
        """

        cursor.execute(
            query,
            (
                categoria_id,
                subcategoria_id,
                nome,
                descricao,
                preco,
                imagem,
                disponivel,
                ordem,
                informacoes_adicionais,
                produto_id,
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
# EXCLUIR PRODUTO
# ==========================================================

def excluir_produto(
    produto_id,
    estabelecimento_id
):

    conexao = get_connection()
    cursor = conexao.cursor()

    try:

        query = """
            DELETE FROM produtos
            WHERE id = %s
              AND estabelecimento_id = %s
        """

        cursor.execute(
            query,
            (
                produto_id,
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
# ALTERAR DISPONIBILIDADE
# ==========================================================

def alterar_disponibilidade(
    produto_id,
    estabelecimento_id,
    disponivel
):

    conexao = get_connection()
    cursor = conexao.cursor()

    try:

        query = """
            UPDATE produtos
            SET disponivel = %s
            WHERE id = %s
              AND estabelecimento_id = %s
        """

        cursor.execute(
            query,
            (
                disponivel,
                produto_id,
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
