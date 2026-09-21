from database.connection import get_connection


def buscar_por_slug(slug):
    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)

    query = """
        SELECT
            id,
            nome,
            slug,
            logo,
            imagem_capa,
            descricao,
            telefone,
            whatsapp,
            endereco,
            ativo
        FROM estabelecimentos
        WHERE slug = %s
          AND ativo = 1
    """

    try:
        cursor.execute(query, (slug,))
        return cursor.fetchone()

    finally:
        cursor.close()
        conexao.close()


def buscar_por_id(estabelecimento_id):
    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)

    query = """
        SELECT
            id,
            nome,
            slug,
            logo,
            imagem_capa,
            descricao,
            telefone,
            whatsapp,
            endereco,
            ativo
        FROM estabelecimentos
        WHERE id = %s
        LIMIT 1
    """

    try:
        cursor.execute(query, (estabelecimento_id,))
        return cursor.fetchone()

    finally:
        cursor.close()
        conexao.close()


def atualizar_estabelecimento(
    estabelecimento_id,
    nome,
    descricao,
    telefone,
    whatsapp,
    endereco,
    logo=None,
    imagem_capa=None
):
    conexao = get_connection()
    cursor = conexao.cursor()

    query = """
        UPDATE estabelecimentos
        SET
            nome = %s,
            descricao = %s,
            telefone = %s,
            whatsapp = %s,
            endereco = %s,
            logo = COALESCE(%s, logo),
            imagem_capa = COALESCE(%s, imagem_capa)
        WHERE id = %s
    """

    try:
        cursor.execute(
            query,
            (
                nome,
                descricao,
                telefone,
                whatsapp,
                endereco,
                logo,
                imagem_capa,
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


def criar_estabelecimento(
    nome,
    slug,
    logo=None,
    imagem_capa=None,
    descricao=None,
    telefone=None,
    whatsapp=None,
    endereco=None
):
    conexao = get_connection()
    cursor = conexao.cursor()

    query = """
        INSERT INTO estabelecimentos (
            nome,
            slug,
            logo,
            imagem_capa,
            descricao,
            telefone,
            whatsapp,
            endereco
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    valores = (
        nome,
        slug,
        logo,
        imagem_capa,
        descricao,
        telefone,
        whatsapp,
        endereco
    )

    try:
        cursor.execute(query, valores)
        conexao.commit()
        return cursor.lastrowid

    except Exception:
        conexao.rollback()
        raise

    finally:
        cursor.close()
        conexao.close()
