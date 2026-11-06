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
from database.billing import assinatura_bloqueada
import re

public = Blueprint("public", __name__)


def acesso_publico_bloqueado(estabelecimento):
    """Verifica se o estabelecimento pode exibir páginas públicas do cardápio."""
    if not estabelecimento or not estabelecimento.get("ativo"):
        return True
    return assinatura_bloqueada(estabelecimento["id"])


def resposta_cardapio_indisponivel():
    return render_template("public/cardapio_indisponivel.html"), 403



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
 
    def cor_valida(valor):
        return bool(valor) and re.fullmatch(r"#[0-9a-fA-F]{6}", valor) is not None
 
    # SE EXISTIR PERSONALIZAÇÃO VÁLIDA, SOBRESCREVE O PADRÃO
 
    if aparencia:
 
        if cor_valida(aparencia["cor_principal"]):
            cor_principal = aparencia["cor_principal"]
 
        if cor_valida(aparencia["cor_secundaria"]):
            cor_secundaria = aparencia["cor_secundaria"]
 
        if cor_valida(aparencia["cor_texto"]):
            cor_texto = aparencia["cor_texto"]
 
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
 
    css = f""":root {{
    --cor-principal: {cor_principal};
    --cor-secundaria: {cor_secundaria};
    --cor-texto: {cor_texto};
    --texto-sobre-principal: {texto_sobre_principal};
    --texto-sobre-secundaria: {texto_sobre_secundaria};
}}
"""
 
    return Response(
        css,
        mimetype="text/css"
    )
 
@public.route("/")
def inicio():

    return render_template(
        "public/inicio.html"
    )


@public.route("/faq")
def faq():

    return render_template(
        "public/faq.html",
        pagina_institucional=True
    )




@public.route("/sobre")
def sobre():

    return render_template(
        "public/sobre.html",
        pagina_institucional=True
    )


@public.route("/termos-de-uso")
def termos_de_uso():

    return render_template(
        "public/termos_uso.html",
        pagina_institucional=True
    )




@public.route("/politica-de-privacidade")
def politica_privacidade():

    return render_template(
        "public/politica_privacidade.html",
        pagina_institucional=True
    )



@public.route("/<slug>")
def estabelecimento(slug):

    estabelecimento = buscar_por_slug(slug)

    if estabelecimento is None:
        return "Estabelecimento não encontrado", 404

    if acesso_publico_bloqueado(estabelecimento):
        return resposta_cardapio_indisponivel()

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

@public.route("/<slug>/cardapio")
def cardapio(slug):

    estabelecimento = buscar_por_slug(slug)

    if estabelecimento is None:
        return render_template(
            "public/cardapio_indisponivel.html"
        ), 404

    if acesso_publico_bloqueado(estabelecimento):
        return resposta_cardapio_indisponivel()

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


@public.route(
    "/<slug>/cardapio/categoria/<int:categoria_id>"
)
def categoria(slug, categoria_id):

    estabelecimento = buscar_por_slug(slug)

    if estabelecimento is None:
        return "Estabelecimento não encontrado", 404

    if acesso_publico_bloqueado(estabelecimento):
        return resposta_cardapio_indisponivel()

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



@public.route(
    "/<slug>/cardapio/subcategoria/<int:subcategoria_id>"
)
def subcategoria(slug, subcategoria_id):

    estabelecimento = buscar_por_slug(slug)

    if estabelecimento is None:
        return "Estabelecimento não encontrado", 404

    if acesso_publico_bloqueado(estabelecimento):
        return resposta_cardapio_indisponivel()

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



@public.route("/<slug>/buscar")
def buscar(slug):

    estabelecimento = buscar_por_slug(slug)

    if estabelecimento is None:
        return "Estabelecimento não encontrado", 404

    if acesso_publico_bloqueado(estabelecimento):
        return resposta_cardapio_indisponivel()

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
