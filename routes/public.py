from flask import Blueprint, render_template, request, Response
from database.estabelecimentos import buscar_por_slug
from database.produtos import buscar_por_termo
from database.categorias import (
    buscar_cardapio_por_estabelecimento,
    buscar_categoria_com_produtos,
    buscar_subcategoria_com_produtos
)
from database.horarios import buscar_por_estabelecimento as buscar_horarios_por_estabelecimento
from database.aparencia import buscar_por_estabelecimento as buscar_aparencia_por_estabelecimento
from database.redes_sociais import buscar_por_estabelecimento as buscar_redes_sociais_por_estabelecimento


public = Blueprint("public", __name__)



# ============================================================
# CSS PERSONALIZADO DO ESTABELECIMENTO
# ============================================================

@public.route("/<slug>/aparencia.css")
def aparencia_css(slug):

    estabelecimento = buscar_por_slug(slug)

    if estabelecimento is None:
        return Response(
            "",
            mimetype="text/css"
        )

    aparencia = buscar_aparencia_por_estabelecimento(
        estabelecimento["id"]
    )

    # CORES PADRÃO DO LA CARTA

    cor_principal = "#310505"
    cor_secundaria = "#B89B5E"
    cor_texto = "#1F1F1F"

    # SE EXISTIR PERSONALIZAÇÃO, SOBRESCREVE O PADRÃO

    if aparencia:

        if aparencia["cor_principal"]:
            cor_principal = aparencia["cor_principal"]

        if aparencia["cor_secundaria"]:
            cor_secundaria = aparencia["cor_secundaria"]

        if aparencia["cor_texto"]:
            cor_texto = aparencia["cor_texto"]

    # ============================================================
    # CALCULA AUTOMATICAMENTE UMA COR DE TEXTO LEGÍVEL
    # ============================================================

    def cor_contraste(hex_color):

        hex_color = hex_color.lstrip("#")

        if len(hex_color) != 6:
            return "#FFFFFF"

        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
        except ValueError:
            return "#FFFFFF"

        luminancia = (
            (0.299 * r) +
            (0.587 * g) +
            (0.114 * b)
        )

        if luminancia > 186:
            return "#1F1F1F"

        return "#FFFFFF"

    texto_sobre_principal = cor_contraste(cor_principal)
    texto_sobre_secundaria = cor_contraste(cor_secundaria)

    css = f"""
    /* =========================
       CORES PERSONALIZADAS
       ========================= */

    /* CATEGORIAS */

    .menuCategorias a {{
        background-color: {cor_principal} !important;
        color: {texto_sobre_principal} !important;
    }}

    .menuCategorias a:hover {{
        background-color: {cor_principal} !important;
        color: {texto_sobre_principal} !important;
    }}


    /* TÍTULOS */

    .menuSection h2 {{
        color: {cor_principal} !important;
    }}

    .menuHeader .label {{
        color: {cor_principal} !important;
    }}

    .menuHeader h1 {{
        color: {cor_principal} !important;
    }}


    /* PRODUTOS */

    .produto,
    .cardProdutoCategoria {{
        background-color: {cor_principal} !important;
    }}

    .produto h3,
    .infoProdutoCategoria h2 {{
        color: {texto_sobre_principal} !important;
    }}

    .produto p,
    .descricaoProdutoCategoria {{
        color: {texto_sobre_principal} !important;
    }}

    .informacoesAdicionaisCategoria {{
        color: {texto_sobre_principal} !important;
    }}

    .produto strong,
    .precoProdutoCategoria {{
        color: {cor_secundaria} !important;
    }}


    /* BUSCA */

    .paginaBusca h2 {{
        color: {cor_principal} !important;
        border-bottom-color: {cor_secundaria} !important;
    }}

    .resultadosBusca .cardProduto {{
        background-color: {cor_principal} !important;
    }}

    .resultadosBusca .infoProduto h3 {{
        color: {texto_sobre_principal} !important;
    }}

    .resultadosBusca .descricaoProduto {{
        color: {texto_sobre_principal} !important;
    }}

    .resultadosBusca .precoProduto {{
        color: {cor_secundaria} !important;
    }}


    /* HEADER */

    .public-header {{
        background-color: {cor_principal} !important;
    }}


    /* ASIDE */

    .asideBasePublic {{
        background-color: {cor_principal} !important;
    }}

    .asideBasePublic a {{
        color: {texto_sobre_principal} !important;
    }}


    /* FOOTER */

    .navegacaoFooter {{
        background-color: {cor_principal} !important;
    }}

    .footerItem {{
        color: {texto_sobre_principal} !important;
    }}

    .footerItem:hover,
    .footerItem:active {{
        color: {texto_sobre_secundaria} !important;
    }}


    /* LOGO */

    .logo span {{
        color: {cor_secundaria} !important;
    }}


    /* BUSCA DO HEADER */

    .search {{
        border-color: {cor_secundaria} !important;
    }}

    .search button {{
        background-color: {cor_secundaria} !important;
        color: {texto_sobre_secundaria} !important;
    }}


    /* TEXTOS GERAIS */

    .mainPublic {{
        color: {cor_texto} !important;
    }}


    /* HERO */

    .logoHero {{
        border-color: {cor_secundaria} !important;
        background-color: {cor_principal} !important;
    }}

    .horariosHero summary {{
        color: {cor_secundaria} !important;
    }}

    .horariosHero summary::after {{
        color: {texto_sobre_secundaria} !important;
        background-color: {cor_secundaria} !important;
    }}

    .botaoVerCardapio,
    .sobre-cta-button {{
        color: {texto_sobre_secundaria} !important;
        background-color: {cor_secundaria} !important;
    }}
    """

    return Response(
        css,
        mimetype="text/css"
    )
# ============================================================
# INÍCIO GERAL DO LA CARTA
# ============================================================
@public.route("/")
def inicio():

    return render_template(
        "public/inicio.html"
    )


# ============================================================
# FAQ DO LA CARTA
# ============================================================

@public.route("/faq")
def faq():

    return render_template(
        "public/faq.html",
        pagina_institucional=True
    )


# ============================================================
# SOBRE O LA CARTA
# ============================================================

@public.route("/sobre")
def sobre():

    return render_template(
        "public/sobre.html",
        pagina_institucional=True
    )
# ============================================================
# TERMOS DE USO
# ============================================================

@public.route("/termos-de-uso")
def termos_de_uso():

    return render_template(
        "public/termos_uso.html",
        pagina_institucional=True
    )


# ============================================================
# POLÍTICA DE PRIVACIDADE
# ============================================================

@public.route("/politica-de-privacidade")
def politica_privacidade():

    return render_template(
        "public/politica_privacidade.html",
        pagina_institucional=True
    )


# ============================================================
# INÍCIO DO ESTABELECIMENTO
# ============================================================

@public.route("/<slug>")
def estabelecimento(slug):

    estabelecimento = buscar_por_slug(slug)

    if estabelecimento is None:
        return "Estabelecimento não encontrado", 404

    horarios = buscar_horarios_por_estabelecimento(
        estabelecimento["id"]
    )

    aparencia = buscar_aparencia_por_estabelecimento(
        estabelecimento["id"]
    )
    redes = buscar_redes_sociais_por_estabelecimento(
        estabelecimento["id"]
    )

    redes_ativas = [
        rede for rede in redes
        if rede["ativo"] == 1
    ]
    return render_template(
        "public/estabelecimento.html",
        estabelecimento=estabelecimento,
        horarios=horarios,
        aparencia=aparencia,
        redes=redes_ativas
    )


# ============================================================
# CARDÁPIO DO ESTABELECIMENTO
# ============================================================

@public.route("/<slug>/cardapio")
def cardapio(slug):

    estabelecimento = buscar_por_slug(slug)

    if estabelecimento is None:
        return "Estabelecimento não encontrado", 404

    categorias = buscar_cardapio_por_estabelecimento(
        estabelecimento["id"]
    )

    aparencia = buscar_aparencia_por_estabelecimento(
        estabelecimento["id"]
    )

    return render_template(
        "public/cardapio.html",
        estabelecimento=estabelecimento,
        categorias=categorias,
        aparencia=aparencia
    )


# ============================================================
# CATEGORIA DO CARDÁPIO
# ============================================================

@public.route(
    "/<slug>/cardapio/categoria/<int:categoria_id>"
)
def categoria(slug, categoria_id):

    estabelecimento = buscar_por_slug(slug)

    if estabelecimento is None:
        return "Estabelecimento não encontrado", 404

    categoria = buscar_categoria_com_produtos(
        categoria_id,
        estabelecimento["id"]
    )

    if categoria is None:
        return "Categoria não encontrada", 404

    aparencia = buscar_aparencia_por_estabelecimento(
        estabelecimento["id"]
    )

    return render_template(
        "public/categoria.html",
        estabelecimento=estabelecimento,
        categoria=categoria,
        aparencia=aparencia
    )


# ============================================================
# SUBCATEGORIA DO CARDÁPIO
# ============================================================

@public.route(
    "/<slug>/cardapio/subcategoria/<int:subcategoria_id>"
)
def subcategoria(slug, subcategoria_id):

    estabelecimento = buscar_por_slug(slug)

    if estabelecimento is None:
        return "Estabelecimento não encontrado", 404

    subcategoria = buscar_subcategoria_com_produtos(
        subcategoria_id,
        estabelecimento["id"]
    )

    if subcategoria is None:
        return "Subcategoria não encontrada", 404

    aparencia = buscar_aparencia_por_estabelecimento(
        estabelecimento["id"]
    )

    return render_template(
        "public/subcategoria.html",
        estabelecimento=estabelecimento,
        subcategoria=subcategoria,
        aparencia=aparencia
    )


# ============================================================
# BUSCA DE PRODUTOS
# ============================================================

@public.route("/<slug>/buscar")
def buscar(slug):

    estabelecimento = buscar_por_slug(slug)

    if estabelecimento is None:
        return "Estabelecimento não encontrado", 404

    termo = request.args.get(
        "q",
        ""
    ).strip()

    produtos = []

    if termo:

        produtos = buscar_por_termo(
            estabelecimento["id"],
            termo
        )

    aparencia = buscar_aparencia_por_estabelecimento(
        estabelecimento["id"]
    )

    return render_template(
        "public/busca.html",
        estabelecimento=estabelecimento,
        produtos=produtos,
        termo=termo,
        aparencia=aparencia
    )