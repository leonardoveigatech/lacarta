from database.connection import get_connection


# ==========================================================
# BUSCAR CATEGORIAS DO ESTABELECIMENTO
# ==========================================================

def buscar_por_estabelecimento(estabelecimento_id):

    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)

    try:

        query = """
            SELECT
                id,
                estabelecimento_id,
                nome,
                ordem,
                ativo,
                disponivel
            FROM categorias
            WHERE estabelecimento_id = %s
            ORDER BY ordem ASC, id ASC
        """

        cursor.execute(
            query,
            (estabelecimento_id,)
        )

        categorias = cursor.fetchall()

    finally:

        cursor.close()
        conexao.close()

    return categorias


# ==========================================================
# BUSCAR CATEGORIA POR ID
# ==========================================================

def buscar_por_id(
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
                nome,
                ordem,
                ativo,
                disponivel
            FROM categorias
            WHERE id = %s
              AND estabelecimento_id = %s
        """

        cursor.execute(
            query,
            (
                categoria_id,
                estabelecimento_id
            )
        )

        return cursor.fetchone()

    finally:

        cursor.close()
        conexao.close()


# ==========================================================
# CRIAR CATEGORIA
# ==========================================================

def criar_categoria(
    estabelecimento_id,
    nome,
    ordem
):

    conexao = get_connection()
    cursor = conexao.cursor()

    try:

        query = """
            INSERT INTO categorias (
                estabelecimento_id,
                nome,
                ordem,
                ativo,
                disponivel
            )
            VALUES (
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
                nome,
                ordem
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
# ATUALIZAR CATEGORIA
# ==========================================================

def atualizar_categoria(
    categoria_id,
    estabelecimento_id,
    nome,
    ordem
):

    conexao = get_connection()
    cursor = conexao.cursor()

    try:

        query = """
            UPDATE categorias
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
                categoria_id,
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

def alterar_disponibilidade_categoria(
    categoria_id,
    estabelecimento_id,
    disponivel
):

    conexao = get_connection()
    cursor = conexao.cursor()

    try:

        query = """
            UPDATE categorias
            SET disponivel = %s
            WHERE id = %s
              AND estabelecimento_id = %s
        """

        cursor.execute(
            query,
            (
                disponivel,
                categoria_id,
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
# EXCLUIR CATEGORIA
# ==========================================================

def excluir_categoria(
    categoria_id,
    estabelecimento_id
):

    conexao = get_connection()
    cursor = conexao.cursor()

    try:

        # --------------------------------------------------
        # VERIFICAR PRODUTOS
        # --------------------------------------------------

        query = """
            SELECT COUNT(*) AS total
            FROM produtos
            WHERE categoria_id = %s
              AND estabelecimento_id = %s
        """

        cursor.execute(
            query,
            (
                categoria_id,
                estabelecimento_id
            )
        )

        resultado = cursor.fetchone()

        total_produtos = resultado[0]

        if total_produtos > 0:

            return False

        # --------------------------------------------------
        # EXCLUIR SUBCATEGORIAS
        # --------------------------------------------------

        query = """
            DELETE FROM subcategorias
            WHERE categoria_id = %s
              AND estabelecimento_id = %s
        """

        cursor.execute(
            query,
            (
                categoria_id,
                estabelecimento_id
            )
        )

        # --------------------------------------------------
        # EXCLUIR CATEGORIA
        # --------------------------------------------------

        query = """
            DELETE FROM categorias
            WHERE id = %s
              AND estabelecimento_id = %s
        """

        cursor.execute(
            query,
            (
                categoria_id,
                estabelecimento_id
            )
        )

        conexao.commit()

        return True

    except Exception:

        conexao.rollback()
        raise

    finally:

        cursor.close()
        conexao.close()


# ==========================================================
# CARDÁPIO PÚBLICO
# ==========================================================

def buscar_cardapio_por_estabelecimento(
    estabelecimento_id
):

    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)

    try:

        query = """
            SELECT
                c.id AS categoria_id,
                c.nome AS categoria_nome,
                c.ordem AS categoria_ordem,

                sc.id AS subcategoria_id,
                sc.nome AS subcategoria_nome,
                sc.ordem AS subcategoria_ordem

            FROM categorias c

            LEFT JOIN subcategorias sc
                ON sc.categoria_id = c.id
                AND sc.estabelecimento_id = c.estabelecimento_id
                AND sc.ativo = 1
                AND sc.disponivel = 1

            WHERE c.estabelecimento_id = %s
              AND c.ativo = 1
              AND c.disponivel = 1

            ORDER BY
                c.ordem ASC,
                c.id ASC,
                sc.ordem ASC,
                sc.id ASC
        """

        cursor.execute(
            query,
            (estabelecimento_id,)
        )

        resultados = cursor.fetchall()

    finally:

        cursor.close()
        conexao.close()

    categorias = {}

    for resultado in resultados:

        categoria_id = resultado["categoria_id"]

        if categoria_id not in categorias:

            categorias[categoria_id] = {
                "id": categoria_id,
                "nome": resultado["categoria_nome"],
                "ordem": resultado["categoria_ordem"],
                "subcategorias": []
            }

        subcategoria_id = resultado["subcategoria_id"]

        if subcategoria_id is not None:

            categorias[categoria_id]["subcategorias"].append({
                "id": subcategoria_id,
                "nome": resultado["subcategoria_nome"],
                "ordem": resultado["subcategoria_ordem"]
            })

    return list(categorias.values())


# ==========================================================
# CATEGORIA COM PRODUTOS
# ==========================================================

def buscar_categoria_com_produtos(
    categoria_id,
    estabelecimento_id
):

    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)

    try:

        # --------------------------------------------------
        # CATEGORIA
        # --------------------------------------------------

        query_categoria = """
            SELECT
                id,
                nome,
                ordem
            FROM categorias
            WHERE id = %s
              AND estabelecimento_id = %s
              AND ativo = 1
              AND disponivel = 1
        """

        cursor.execute(
            query_categoria,
            (
                categoria_id,
                estabelecimento_id
            )
        )

        categoria = cursor.fetchone()

        if categoria is None:
            return None

        # --------------------------------------------------
        # SUBCATEGORIAS
        # --------------------------------------------------

        query_subcategorias = """
            SELECT
                id,
                nome,
                ordem
            FROM subcategorias
            WHERE categoria_id = %s
              AND estabelecimento_id = %s
              AND ativo = 1
              AND disponivel = 1
            ORDER BY ordem ASC, id ASC
        """

        cursor.execute(
            query_subcategorias,
            (
                categoria_id,
                estabelecimento_id
            )
        )

        subcategorias = cursor.fetchall()

        # --------------------------------------------------
        # PRODUTOS DIRETOS DA CATEGORIA
        # --------------------------------------------------

        query_produtos = """
            SELECT
                id,
                nome,
                descricao,
                preco,
                imagem,
                informacoes_adicionais
            FROM produtos
            WHERE categoria_id = %s
              AND estabelecimento_id = %s
              AND subcategoria_id IS NULL
              AND disponivel = 1
            ORDER BY ordem ASC, id ASC
        """

        cursor.execute(
            query_produtos,
            (
                categoria_id,
                estabelecimento_id
            )
        )

        produtos = cursor.fetchall()

    finally:

        cursor.close()
        conexao.close()

    categoria["subcategorias"] = subcategorias
    categoria["produtos"] = produtos

    return categoria


# ==========================================================
# SUBCATEGORIA COM PRODUTOS
# ==========================================================

def buscar_subcategoria_com_produtos(
    subcategoria_id,
    estabelecimento_id
):

    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)

    try:

        query = """
            SELECT
                sc.id AS subcategoria_id,
                sc.nome AS subcategoria_nome,

                c.id AS categoria_id,
                c.nome AS categoria_nome

            FROM subcategorias sc

            INNER JOIN categorias c
                ON c.id = sc.categoria_id
                AND c.estabelecimento_id = sc.estabelecimento_id

            WHERE sc.id = %s
              AND sc.estabelecimento_id = %s
              AND sc.ativo = 1
              AND sc.disponivel = 1
              AND c.ativo = 1
              AND c.disponivel = 1
        """

        cursor.execute(
            query,
            (
                subcategoria_id,
                estabelecimento_id
            )
        )

        subcategoria = cursor.fetchone()

        if subcategoria is None:
            return None

        # --------------------------------------------------
        # PRODUTOS
        # --------------------------------------------------

        query_produtos = """
            SELECT
                id,
                nome,
                descricao,
                preco,
                imagem,
                informacoes_adicionais
            FROM produtos
            WHERE subcategoria_id = %s
              AND estabelecimento_id = %s
              AND disponivel = 1
            ORDER BY ordem ASC, id ASC
        """

        cursor.execute(
            query_produtos,
            (
                subcategoria_id,
                estabelecimento_id
            )
        )

        produtos = cursor.fetchall()

    finally:

        cursor.close()
        conexao.close()

    subcategoria["produtos"] = produtos

    return subcategoria