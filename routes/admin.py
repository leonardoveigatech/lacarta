from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    current_app
)
from utils.rate_limit import limite_excedido, identificador_cliente

import os
import re
from datetime import datetime
from urllib.parse import urlparse
from decimal import Decimal, InvalidOperation

from werkzeug.utils import secure_filename
from PIL import Image, UnidentifiedImageError
from config import MAX_UPLOAD_BYTES, MAX_IMAGE_PIXELS
from utils.csrf import validar_csrf_token
from utils.email import enviar_email

from database.aparencia import (
    buscar_por_estabelecimento as buscar_aparencia_por_estabelecimento,
    criar as criar_aparencia,
    atualizar as atualizar_aparencia
)

from database.usuarios import (
    buscar_por_email,
    buscar_por_id as buscar_usuario_por_id,
    verificar_senha, atualizar_nome, atualizar_email, atualizar_senha
)
from database.password_reset import (
    criar_token as criar_token_recuperacao,
    buscar_token as buscar_token_recuperacao,
    marcar_como_usado as marcar_token_recuperacao_usado,
    invalidar_tokens_usuario as invalidar_tokens_recuperacao
)
from database.email_change import (
    criar_token as criar_token_email,
    buscar_token as buscar_token_email,
    invalidar_tokens_usuario as invalidar_tokens_email
)

from database.estabelecimentos import (
    buscar_por_id as buscar_estabelecimento_por_id,
    atualizar_estabelecimento
)

from database.categorias import (
    buscar_por_estabelecimento,
    buscar_por_id as buscar_categoria_por_id,
    criar_categoria,
    atualizar_categoria,
    excluir_categoria,
    alterar_disponibilidade_categoria
)

from database.subcategorias import (
    buscar_por_categoria as buscar_subcategorias_por_categoria,
    buscar_por_id as buscar_subcategoria_por_id,
    criar_subcategoria,
    atualizar_subcategoria,
    excluir_subcategoria
)

from database.produtos import (
    buscar_todos_por_estabelecimento,
    buscar_por_categoria as buscar_produtos_por_categoria,
    buscar_por_id as buscar_produto_por_id,
    criar_produto,
    atualizar_produto,
    excluir_produto,
    alterar_disponibilidade,
    buscar_por_subcategoria as buscar_produtos_por_subcategoria
)
from database.horarios import (
    buscar_por_estabelecimento as buscar_horarios_por_estabelecimento,
    salvar_horarios
)
from database.redes_sociais import (
    buscar_por_estabelecimento as buscar_redes_sociais_por_estabelecimento,
    buscar_por_id as buscar_rede_social_por_id,
    criar as criar_rede_social,
    atualizar as atualizar_rede_social,
    excluir as excluir_rede_social,
    alterar_status as alterar_status_rede_social
)
from database.email_change import (
    criar_token as criar_token_email,
    buscar_token as buscar_token_email,
    invalidar_tokens_usuario as invalidar_tokens_email,  
    marcar_como_usado as marcar_token_email_usado

)


EXTENSOES_IMAGENS_ESTABELECIMENTO = {".jpg", ".jpeg", ".png", ".webp"}
LIMITE_NOME_ESTABELECIMENTO = 100
LIMITE_DESCRICAO_ESTABELECIMENTO = 1000
LIMITE_TELEFONE = 30
LIMITE_WHATSAPP = 30
LIMITE_ENDERECO = 255
LIMITE_NOME_CATEGORIA = 100
LIMITE_NOME_SUBCATEGORIA = 100
LIMITE_NOME_PRODUTO = 150
LIMITE_DESCRICAO_PRODUTO = 2000
LIMITE_INFORMACOES_PRODUTO = 2000
LIMITE_NOME_USUARIO = 100
LIMITE_EMAIL = 254
LIMITE_URL = 2048

def imagem_valida_estabelecimento(arquivo, extensao):
    formatos = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}
    try:
        arquivo.stream.seek(0, 2)
        if arquivo.stream.tell() > MAX_UPLOAD_BYTES:
            return False
        arquivo.stream.seek(0)
        imagem = Image.open(arquivo.stream)
        if imagem.format != formatos[extensao]:
            return False
        if imagem.width * imagem.height > MAX_IMAGE_PIXELS:
            return False
        imagem.verify()
        arquivo.stream.seek(0)
        return True
    except (UnidentifiedImageError, OSError, ValueError):
        return False


def salvar_imagem_estabelecimento(arquivo, pasta):
    if not arquivo or not arquivo.filename:
        return None

    nome_seguro = secure_filename(arquivo.filename)

    if not nome_seguro:
        raise ValueError("Nome de arquivo inválido.")

    extensao = os.path.splitext(nome_seguro)[1].lower()

    if extensao not in EXTENSOES_IMAGENS_ESTABELECIMENTO:
        raise ValueError("Formato de imagem não permitido. Use JPG, JPEG, PNG ou WEBP.")

    if not imagem_valida_estabelecimento(arquivo, extensao):
        raise ValueError("O arquivo enviado não é uma imagem válida.")

    nome_final = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}{extensao}"
    pasta_completa = os.path.join("static", "uploads", pasta)
    os.makedirs(pasta_completa, exist_ok=True)

    caminho_completo = os.path.join(pasta_completa, nome_final)
    arquivo.save(caminho_completo)

    return os.path.join("uploads", pasta, nome_final).replace("\\", "/")


admin = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


def usuario_logado():

    usuario_id = session.get("usuario_id")

    if usuario_id is None:
        return None

    usuario = buscar_usuario_por_id(usuario_id)

    if usuario is None:
        session.clear()
        return None

    senha_alterada_em_sessao = session.get(
        "senha_alterada_em"
    )

    senha_alterada_em_banco = usuario[
        "senha_alterada_em"
    ]

    valor_banco = (
        senha_alterada_em_banco.isoformat()
        if senha_alterada_em_banco is not None
        else None
    )

    if senha_alterada_em_sessao != valor_banco:
        session.clear()
        return None

    if not usuario["ativo"]:
        session.clear()
        return None

    if not usuario["email_confirmado"]:
        session.clear()
        return None

    estabelecimento = buscar_estabelecimento_por_id(
        usuario["estabelecimento_id"]
    )

    if estabelecimento is None or not estabelecimento["ativo"]:
        session.clear()
        return None

    return usuario


def email_valido(email):
    return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) is not None


def token_recuperacao_valido(token):
    return (
        token is not None
        and not token["usado"]
        and token["expira_em"] >= datetime.now()
    )


def token_email_valido(token):
    return (
        token is not None
        and not token["usado"]
        and token["expira_em"] >= datetime.now()
    )


@admin.route("/")
def dashboard():

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )

    estabelecimento = buscar_estabelecimento_por_id(
        usuario["estabelecimento_id"]
    )

    if estabelecimento is None:
        session.clear()
        return redirect(
            url_for("admin.login")
        )

    if not estabelecimento["ativo"]:
        session.clear()
        return redirect(
            url_for("admin.login")
        )

    return render_template(
        "admin/dashboard.html",
        usuario=usuario,
        estabelecimento=estabelecimento
    )

@admin.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        token_csrf = request.form.get("csrf_token")
        validar_csrf_token(token_csrf)

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        senha = request.form.get(
            "senha",
            ""
        )

        if limite_excedido(
            "login", f"{identificador_cliente()}:{email}", 5, 900
        ):
            return "Muitas tentativas. Tente novamente em 15 minutos.", 429

        usuario = buscar_por_email(
            email
        )

        if usuario is None:
            return "E-mail ou senha inválidos", 401

        if not usuario["ativo"]:
            return "E-mail ou senha inválidos", 401

        estabelecimento = buscar_estabelecimento_por_id(
            usuario["estabelecimento_id"]
        )

        if (
            estabelecimento is None
            or not estabelecimento["ativo"]
        ):
            return "E-mail ou senha inválidos", 401

        if not verificar_senha(
            senha,
            usuario["senha"]
        ):
            return "E-mail ou senha inválidos", 401

        if not usuario["email_confirmado"]:
            return "E-mail ou senha inválidos", 401

        session.clear()
        session.permanent = True

        session["usuario_id"] = usuario["id"]

        session["estabelecimento_id"] = (
            usuario["estabelecimento_id"]
        )

        if usuario["senha_alterada_em"] is not None:

            session["senha_alterada_em"] = (
                usuario["senha_alterada_em"].isoformat()
            )

        else:

            session["senha_alterada_em"] = None

        return redirect(
            url_for("admin.dashboard")
        )

    return render_template(
        "admin/login.html"
    )

@admin.route("/logout", methods=["POST"])
def logout():

    token_csrf = request.form.get("csrf_token")
    validar_csrf_token(token_csrf)

    session.clear()

    return redirect(
        url_for("admin.login")
    )


@admin.route("/estabelecimento")
def estabelecimento():

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )

    estabelecimento = buscar_estabelecimento_por_id(
        usuario["estabelecimento_id"]
    )

    if estabelecimento is None:
        return "Estabelecimento não encontrado", 404

    return render_template(
        "admin/estabelecimento.html",
        usuario=usuario,
        estabelecimento=estabelecimento
    )


@admin.route(
    "/estabelecimento/editar",
    methods=["POST"]
)
def editar_estabelecimento():

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )
    if request.method == "POST":

     token = request.form.get("csrf_token")
    validar_csrf_token(token)

    estabelecimento_id = usuario["estabelecimento_id"]

    nome = request.form.get(
        "nome",
        ""
    ).strip()

    descricao = request.form.get(
        "descricao",
        ""
    ).strip()

    telefone = request.form.get(
        "telefone",
        ""
    ).strip()

    whatsapp = request.form.get(
        "whatsapp",
        ""
    ).strip()

    endereco = request.form.get(
        "endereco",
        ""
    ).strip()

    if not nome:
        return "O nome do estabelecimento é obrigatório", 400
    if len(nome) > LIMITE_NOME_ESTABELECIMENTO:
        return "O nome do estabelecimento é muito longo.", 400

    if len(descricao) > LIMITE_DESCRICAO_ESTABELECIMENTO:
        return "A descrição do estabelecimento é muito longa.", 400

    if len(telefone) > LIMITE_TELEFONE:
        return "O telefone é muito longo.", 400

    if len(whatsapp) > LIMITE_WHATSAPP:
        return "O WhatsApp é muito longo.", 400

    if len(endereco) > LIMITE_ENDERECO:
        return "O endereço é muito longo.", 400

    logo = request.files.get("logo")

    imagem_capa = request.files.get("imagemCapa")

    if not imagem_capa:
        imagem_capa = request.files.get("imagem_capa")

    try:
        logo_path = salvar_imagem_estabelecimento(
            logo,
            "logos"
        )

        capa_path = salvar_imagem_estabelecimento(
            imagem_capa,
            "capas"
        )

        atualizar_estabelecimento(
            estabelecimento_id,
            nome,
            descricao,
            telefone,
            whatsapp,
            endereco,
            logo_path,
            capa_path
        )

    except ValueError as erro:
        flash(
            str(erro),
            "error"
        )

        return redirect(
            url_for("admin.estabelecimento")
        )

    except Exception:
        flash(
            "Não foi possível atualizar o estabelecimento.",
            "error"
        )

        return redirect(
            url_for("admin.estabelecimento")
        )

    flash(
        "Estabelecimento atualizado com sucesso.",
        "success"
    )

    return redirect(
        url_for("admin.estabelecimento")
    )



@admin.route("/categorias")
def categorias():

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )

    categorias = buscar_por_estabelecimento(
        usuario["estabelecimento_id"]
    )

    return render_template(
        "admin/categorias.html",
        usuario=usuario,
        categorias=categorias
    )


@admin.route(
    "/categorias/<int:categoria_id>"
)
def visualizar_categoria(categoria_id):

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )

    estabelecimento_id = usuario["estabelecimento_id"]

    categoria = buscar_categoria_por_id(
        categoria_id,
        estabelecimento_id
    )

    if categoria is None:
        return "Categoria não encontrada", 404

    subcategorias = buscar_subcategorias_por_categoria(
        categoria_id,
        estabelecimento_id
    )

    produtos = buscar_produtos_por_categoria(
        categoria_id,
        estabelecimento_id
    )

    produtos_sem_subcategoria = [
        produto
        for produto in produtos
        if produto["subcategoria_id"] is None
    ]

    return render_template(
        "admin/categoria.html",
        usuario=usuario,
        categoria=categoria,
        subcategorias=subcategorias,
        produtos=produtos_sem_subcategoria
    )



@admin.route(
    "/categorias/nova",
    methods=["GET", "POST"]
)
def nova_categoria():

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )

    if request.method == "POST":
        token_csrf = request.form.get("csrf_token")
        validar_csrf_token(token_csrf)

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        ordem = request.form.get(
            "ordem",
            "0"
        ).strip()

        if not nome:
            return "O nome da categoria é obrigatório", 400
        if len(nome) > LIMITE_NOME_CATEGORIA:
            return "O nome da categoria é muito longo.", 400

        try:
            ordem = int(ordem)
        except ValueError:
            ordem = 0

        if ordem < 0:
            ordem = 0

        criar_categoria(
            usuario["estabelecimento_id"],
            nome,
            ordem
        )

        return redirect(
            url_for("admin.categorias")
        )

    return render_template(
        "admin/nova_categoria.html",
        usuario=usuario
    )


@admin.route(
    "/categorias/editar/<int:categoria_id>",
    methods=["GET", "POST"]
)
def editar_categoria(categoria_id):

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )

    estabelecimento_id = usuario["estabelecimento_id"]

    categoria = buscar_categoria_por_id(
        categoria_id,
        estabelecimento_id
    )

    if categoria is None:
        return "Categoria não encontrada", 404

    if request.method == "POST":

        token_csrf = request.form.get("csrf_token")
        validar_csrf_token(token_csrf)

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        ordem = request.form.get(
            "ordem",
            "0"
        ).strip()

        if not nome:
            return "O nome da categoria é obrigatório", 400

        if len(nome) > LIMITE_NOME_CATEGORIA:
            return "O nome da categoria é muito longo.", 400

        try:
            ordem = int(ordem)
        except ValueError:
            ordem = 0

        if ordem < 0:
            ordem = 0

        atualizar_categoria(
            categoria_id,
            estabelecimento_id,
            nome,
            ordem
        )

        return redirect(
            url_for("admin.categorias")
        )

    return render_template(
        "admin/editar_categoria.html",
        usuario=usuario,
        categoria=categoria
    )


@admin.route(
    "/categorias/excluir/<int:categoria_id>",
    methods=["POST"]
)
def excluir_categoria_rota(categoria_id):

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )
    token_csrf = request.form.get("csrf_token")
    validar_csrf_token(token_csrf)

    estabelecimento_id = usuario["estabelecimento_id"]

    categoria = buscar_categoria_por_id(
        categoria_id,
        estabelecimento_id
    )

    if categoria is None:
        return "Categoria não encontrada", 404

    sucesso = excluir_categoria(
        categoria_id,
        estabelecimento_id
    )

    if sucesso:

        flash(
            "Categoria excluída com sucesso.",
            "success"
        )

    else:

        flash(
            "Essa categoria ainda possui produtos. "
            "Remova ou mova os produtos antes de excluí-la.",
            "error"
        )

    return redirect(
        url_for("admin.categorias")
    )


@admin.route(
    "/categorias/disponibilidade/<int:categoria_id>",
    methods=["POST"]
)
def alterar_disponibilidade_categoria_rota(categoria_id):

    usuario = usuario_logado()

    if usuario is None:
        return redirect(url_for("admin.login"))
    token_csrf = request.form.get("csrf_token")
    validar_csrf_token(token_csrf)

    estabelecimento_id = usuario["estabelecimento_id"]

    categoria = buscar_categoria_por_id(
        categoria_id,
        estabelecimento_id
    )

    if categoria is None:
        return "Categoria não encontrada", 404

    nova_disponibilidade = (
        0 if categoria["disponivel"] == 1 else 1
    )

    alterar_disponibilidade_categoria(
        categoria_id,
        estabelecimento_id,
        nova_disponibilidade
    )

    return redirect(
        url_for("admin.categorias")
    )

@admin.route(
    "/categorias/<int:categoria_id>/subcategorias"
)
def subcategorias(categoria_id):

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )

    estabelecimento_id = usuario["estabelecimento_id"]

    categoria = buscar_categoria_por_id(
        categoria_id,
        estabelecimento_id
    )

    if categoria is None:
        return "Categoria não encontrada", 404

    subcategorias = buscar_subcategorias_por_categoria(
        categoria_id,
        estabelecimento_id
    )

    return render_template(
        "admin/subcategorias.html",
        usuario=usuario,
        categoria=categoria,
        subcategorias=subcategorias
    )



@admin.route(
    "/categorias/<int:categoria_id>/subcategorias/json"
)
def subcategorias_json(categoria_id):

    usuario = usuario_logado()

    if usuario is None:
        return {
            "erro": "Não autenticado"
        }, 401

    estabelecimento_id = usuario["estabelecimento_id"]

    categoria = buscar_categoria_por_id(
        categoria_id,
        estabelecimento_id
    )

    if categoria is None:
        return {
            "erro": "Categoria não encontrada"
        }, 404

    subcategorias = buscar_subcategorias_por_categoria(
        categoria_id,
        estabelecimento_id
    )

    return {
        "subcategorias": subcategorias
    }



@admin.route(
    "/categorias/<int:categoria_id>/subcategorias/nova",
    methods=["GET", "POST"]
)
def nova_subcategoria(categoria_id):

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )

    estabelecimento_id = usuario["estabelecimento_id"]

    categoria = buscar_categoria_por_id(
        categoria_id,
        estabelecimento_id
    )

    if categoria is None:
        return "Categoria não encontrada", 404

    if request.method == "POST":
        token_csrf = request.form.get("csrf_token")
        validar_csrf_token(token_csrf)

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        ordem = request.form.get(
            "ordem",
            "0"
        ).strip()

        if not nome:
            return "O nome da subcategoria é obrigatório", 400
        if len(nome) > LIMITE_NOME_SUBCATEGORIA:
            return "O nome da subcategoria é muito longo.", 400

        try:
            ordem = int(ordem)
        except ValueError:
            ordem = 0

        if ordem < 0:
            ordem = 0

        criar_subcategoria(
            estabelecimento_id,
            categoria_id,
            nome,
            ordem
        )

        return redirect(
            url_for(
                "admin.subcategorias",
                categoria_id=categoria_id
            )
        )

    return render_template(
        "admin/nova_subcategoria.html",
        usuario=usuario,
        categoria=categoria
    )


@admin.route(
    "/subcategorias/editar/<int:subcategoria_id>",
    methods=["GET", "POST"]
)
def editar_subcategoria(subcategoria_id):

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )

    estabelecimento_id = usuario["estabelecimento_id"]

    subcategoria = buscar_subcategoria_por_id(
        subcategoria_id,
        estabelecimento_id
    )

    if subcategoria is None:
        return "Subcategoria não encontrada", 404

    categoria = buscar_categoria_por_id(
        subcategoria["categoria_id"],
        estabelecimento_id
    )

    if categoria is None:
        return "Categoria não encontrada", 404

    if request.method == "POST":
        token_csrf = request.form.get("csrf_token")
        validar_csrf_token(token_csrf)

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        ordem = request.form.get(
            "ordem",
            "0"
        ).strip()

        if not nome:
            return "O nome da subcategoria é obrigatório", 400
        if len(nome) > LIMITE_NOME_SUBCATEGORIA:
            return "O nome da subcategoria é muito longo.", 400

        try:
            ordem = int(ordem)
        except ValueError:
            ordem = 0

        if ordem < 0:
            ordem = 0

        atualizar_subcategoria(
            subcategoria_id,
            estabelecimento_id,
            nome,
            ordem
        )

        return redirect(
            url_for(
                "admin.subcategorias",
                categoria_id=subcategoria["categoria_id"]
            )
        )

    return render_template(
        "admin/editar_subcategoria.html",
        usuario=usuario,
        categoria=categoria,
        subcategoria=subcategoria
    )



@admin.route(
    "/subcategorias/excluir/<int:subcategoria_id>",
    methods=["POST"]
)
def excluir_subcategoria_rota(subcategoria_id):

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )
    
    token_csrf = request.form.get("csrf_token")
    validar_csrf_token(token_csrf)

    estabelecimento_id = usuario["estabelecimento_id"]

    subcategoria = buscar_subcategoria_por_id(
        subcategoria_id,
        estabelecimento_id
    )

    if subcategoria is None:
        return "Subcategoria não encontrada", 404

    categoria_id = subcategoria["categoria_id"]

    excluir_subcategoria(
        subcategoria_id,
        estabelecimento_id
    )

    return redirect(
        url_for(
            "admin.subcategorias",
            categoria_id=categoria_id
        )
    )



@admin.route(
    "/subcategorias/<int:subcategoria_id>"
)
def visualizar_subcategoria(subcategoria_id):

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )

    estabelecimento_id = usuario["estabelecimento_id"]

    subcategoria = buscar_subcategoria_por_id(
        subcategoria_id,
        estabelecimento_id
    )

    if subcategoria is None:
        return "Subcategoria não encontrada", 404

    categoria = buscar_categoria_por_id(
        subcategoria["categoria_id"],
        estabelecimento_id
    )

    if categoria is None:
        return "Categoria não encontrada", 404

    produtos = buscar_produtos_por_subcategoria(
        subcategoria_id,
        estabelecimento_id
    )

    return render_template(
        "admin/produtosub.html",
        usuario=usuario,
        categoria=categoria,
        subcategoria=subcategoria,
        produtos=produtos
    )




@admin.route("/produtos")
def produtos():

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )

    estabelecimento_id = usuario["estabelecimento_id"]

    categorias = buscar_por_estabelecimento(
        estabelecimento_id
    )

    todos_produtos = buscar_todos_por_estabelecimento(
        estabelecimento_id
    )

    estrutura = []

    for categoria in categorias:

        categoria_id = categoria["id"]

        subcategorias = buscar_subcategorias_por_categoria(
            categoria_id,
            estabelecimento_id
        )

        produtos_sem_subcategoria = [
            produto
            for produto in todos_produtos
            if produto["categoria_id"] == categoria_id
            and produto["subcategoria_id"] is None
        ]

        for subcategoria in subcategorias:

            subcategoria["produtos"] = [
                produto
                for produto in todos_produtos
                if produto["subcategoria_id"] == subcategoria["id"]
            ]

        estrutura.append({
            "categoria": categoria,
            "subcategorias": subcategorias,
            "produtos_sem_subcategoria": produtos_sem_subcategoria
        })

    return render_template(
        "admin/produtos.html",
        usuario=usuario,
        estrutura=estrutura
    )


# NOVO PRODUTO

@admin.route(
    "/produtos/novo",
    methods=["GET", "POST"]
)
def novo_produto():

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )

    estabelecimento_id = usuario["estabelecimento_id"]

    categorias = buscar_por_estabelecimento(
        estabelecimento_id
    )

    

    if request.method == "GET":

        categoria_id = request.args.get(
            "categoria_id",
            ""
        )

        subcategoria_id = request.args.get(
            "subcategoria_id",
            ""
        )

        subcategorias = []

        if categoria_id:

            try:
                categoria_id = int(categoria_id)
            except ValueError:
                return "Categoria inválida", 400

            categoria = buscar_categoria_por_id(
                categoria_id,
                estabelecimento_id
            )

            if categoria is None:
                return "Categoria inválida", 400

            subcategorias = buscar_subcategorias_por_categoria(
                categoria_id,
                estabelecimento_id
            )

        if subcategoria_id:

            try:
                subcategoria_id = int(subcategoria_id)
            except ValueError:
                return "Subcategoria inválida", 400

            subcategoria = buscar_subcategoria_por_id(
                subcategoria_id,
                estabelecimento_id
            )

            if subcategoria is None:
                return "Subcategoria inválida", 400

            if (
                categoria_id
                and subcategoria["categoria_id"] != categoria_id
            ):
                return (
                    "A subcategoria não pertence "
                    "à categoria selecionada"
                ), 400

            if not categoria_id:

                categoria_id = subcategoria["categoria_id"]

                subcategorias = buscar_subcategorias_por_categoria(
                    categoria_id,
                    estabelecimento_id
                )

        return render_template(
            "admin/novo_produto.html",
            usuario=usuario,
            categorias=categorias,
            subcategorias=subcategorias,
            categoria_id=categoria_id,
            subcategoria_id=subcategoria_id
        )

    
    token_csrf = request.form.get("csrf_token")
    validar_csrf_token(token_csrf)

    nome = request.form.get(
        "nome",
        ""
    ).strip()

    descricao = request.form.get(
        "descricao",
        ""
    ).strip()

    categoria_id = request.form.get(
        "categoria_id",
        ""
    ).strip()

    subcategoria_id = request.form.get(
        "subcategoria_id",
        ""
    ).strip()

    preco = request.form.get(
        "preco",
        "0"
    ).strip()

    ordem = request.form.get(
        "ordem",
        "0"
    ).strip()

    informacoes = request.form.get(
        "informacoes_adicionais",
        ""
    ).strip()

    if not nome:
        return "O nome do produto é obrigatório", 400
    
    if len(nome) > LIMITE_NOME_PRODUTO:
        return "O nome do produto é muito longo.", 400

    if len(descricao) > LIMITE_DESCRICAO_PRODUTO:
        return "A descrição do produto é muito longa.", 400

    if len(informacoes) > LIMITE_INFORMACOES_PRODUTO:
        return "As informações adicionais são muito longas.", 400

    if not categoria_id:
        return "Selecione uma categoria", 400

    try:
        categoria_id = int(categoria_id)
    except ValueError:
        return "Categoria inválida", 400

    categoria = buscar_categoria_por_id(
        categoria_id,
        estabelecimento_id
    )

    if categoria is None:
        return "Categoria inválida", 400

    if subcategoria_id:

        try:
            subcategoria_id = int(subcategoria_id)
        except ValueError:
            return "Subcategoria inválida", 400

        subcategoria = buscar_subcategoria_por_id(
            subcategoria_id,
            estabelecimento_id
        )

        if subcategoria is None:
            return "Subcategoria inválida", 400

        if subcategoria["categoria_id"] != categoria_id:
            return (
                "A subcategoria não pertence "
                "à categoria selecionada"
            ), 400

    else:
        subcategoria_id = None
    try:
        preco = Decimal(preco)
    except InvalidOperation:
        return "Preço inválido", 400

    if not preco.is_finite():
        return "Preço inválido", 400

    if preco < 0:
        return "O preço não pode ser negativo", 400

    if preco.as_tuple().exponent < -2:
        return "O preço deve ter no máximo 2 casas decimais", 400

    try:
        ordem = int(ordem)
    except ValueError:
        ordem = 0

    if ordem < 0:
        ordem = 0

    criar_produto(
        estabelecimento_id,
        categoria_id,
        subcategoria_id,
        nome,
        descricao,
        preco,
        None,
        1,
        ordem,
        informacoes
    )

    if subcategoria_id:

        return redirect(
            url_for(
                "admin.visualizar_subcategoria",
                subcategoria_id=subcategoria_id
            )
        )

    return redirect(
        url_for(
            "admin.visualizar_categoria",
            categoria_id=categoria_id
        )
    )
    
@admin.route(
    "/produtos/editar/<int:produto_id>",
    methods=["GET", "POST"]
)
def editar_produto(produto_id):

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )

    estabelecimento_id = usuario["estabelecimento_id"]

    produto = buscar_produto_por_id(
        produto_id,
        estabelecimento_id
    )

    if produto is None:
        return "Produto não encontrado", 404

    categorias = buscar_por_estabelecimento(
        estabelecimento_id
    )

    categoria_id = produto["categoria_id"]

    subcategorias = buscar_subcategorias_por_categoria(
        categoria_id,
        estabelecimento_id
    )

    if request.method == "POST":

        token_csrf = request.form.get("csrf_token")
        validar_csrf_token(token_csrf)

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        descricao = request.form.get(
            "descricao",
            ""
        ).strip()

        categoria_id = request.form.get(
            "categoria_id",
            ""
        ).strip()

        subcategoria_id = request.form.get(
            "subcategoria_id",
            ""
        ).strip()

        preco = request.form.get(
            "preco",
            "0"
        ).strip()

        ordem = request.form.get(
            "ordem",
            "0"
        ).strip()

        informacoes = request.form.get(
            "informacoes_adicionais",
            ""
        ).strip()

        disponivel = request.form.get(
            "disponivel",
            "1"
        ).strip()

        if not nome:
            return "O nome do produto é obrigatório", 400

        if len(nome) > LIMITE_NOME_PRODUTO:
            return "O nome do produto é muito longo.", 400

        if len(descricao) > LIMITE_DESCRICAO_PRODUTO:
            return "A descrição do produto é muito longa.", 400

        if len(informacoes) > LIMITE_INFORMACOES_PRODUTO:
            return "As informações adicionais são muito longas.", 400

        if not categoria_id:
            return "Selecione uma categoria", 400

        try:
            categoria_id = int(categoria_id)
        except ValueError:
            return "Categoria inválida", 400

        categoria = buscar_categoria_por_id(
            categoria_id,
            estabelecimento_id
        )

        if categoria is None:
            return "Categoria inválida", 400

        if subcategoria_id:

            try:
                subcategoria_id = int(subcategoria_id)
            except ValueError:
                return "Subcategoria inválida", 400

            subcategoria = buscar_subcategoria_por_id(
                subcategoria_id,
                estabelecimento_id
            )

            if subcategoria is None:
                return "Subcategoria inválida", 400

            if subcategoria["categoria_id"] != categoria_id:
                return (
                    "A subcategoria não pertence "
                    "à categoria selecionada"
                ), 400

        else:
            subcategoria_id = None

        try:
            preco = Decimal(preco)
        except InvalidOperation:
            return "Preço inválido", 400

        if not preco.is_finite():
            return "Preço inválido", 400

        if preco < 0:
            return "O preço não pode ser negativo", 400

        if preco.as_tuple().exponent < -2:
            return (
                "O preço deve ter no máximo 2 casas decimais"
            ), 400

        try:
            ordem = int(ordem)
        except ValueError:
            ordem = 0

        if ordem < 0:
            ordem = 0

        try:
            disponivel = int(disponivel)
        except ValueError:
            return "Disponibilidade inválida", 400

        if disponivel not in (0, 1):
            return "Disponibilidade inválida", 400

        atualizar_produto(
            produto_id,
            estabelecimento_id,
            categoria_id,
            subcategoria_id,
            nome,
            descricao,
            preco,
            produto["imagem"],
            disponivel,
            ordem,
            informacoes
        )

        return redirect(
            url_for("admin.produtos")
        )

    return render_template(
        "admin/editar_produto.html",
        usuario=usuario,
        produto=produto,
        categorias=categorias,
        subcategorias=subcategorias
    )




@admin.route(
    "/produtos/excluir/<int:produto_id>",
    methods=["POST"]
)
def excluir_produto_rota(produto_id):

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )
    token_csrf = request.form.get("csrf_token")
    validar_csrf_token(token_csrf)

    estabelecimento_id = usuario["estabelecimento_id"]

    produto = buscar_produto_por_id(
        produto_id,
        estabelecimento_id
    )

    if produto is None:
        return "Produto não encontrado", 404

    categoria_id = produto["categoria_id"]
    subcategoria_id = produto["subcategoria_id"]

    excluir_produto(
        produto_id,
        estabelecimento_id
    )

    if subcategoria_id:

        return redirect(
            url_for(
                "admin.visualizar_subcategoria",
                subcategoria_id=subcategoria_id
            )
        )

    if categoria_id:

        return redirect(
            url_for(
                "admin.visualizar_categoria",
                categoria_id=categoria_id
            )
        )

    return redirect(
        url_for("admin.produtos")
    )



# ==========================================================

@admin.route(
    "/produtos/ativar/<int:produto_id>",
    methods=["POST"]
)
def ativar_produto(produto_id):

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )
    token_csrf = request.form.get("csrf_token")
    validar_csrf_token(token_csrf)

    estabelecimento_id = usuario["estabelecimento_id"]

    alterar_disponibilidade(
        produto_id,
        estabelecimento_id,
        1
    )

    return redirect(
        url_for("admin.produtos")
    )



@admin.route(
    "/produtos/desativar/<int:produto_id>",
    methods=["POST"]
)
def desativar_produto(produto_id):

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )
    token_csrf = request.form.get("csrf_token")
    validar_csrf_token(token_csrf)

    estabelecimento_id = usuario["estabelecimento_id"]

    alterar_disponibilidade(
        produto_id,
        estabelecimento_id,
        0
    )

    return redirect(
        url_for("admin.produtos")
    )


@admin.route("/aparencia", methods=["GET", "POST"])
def aparencia():
    usuario = usuario_logado()

    if usuario is None:
        return redirect(url_for("admin.login"))

    estabelecimento_id = usuario["estabelecimento_id"]

    aparencia_atual = buscar_aparencia_por_estabelecimento(
        estabelecimento_id
    )

    if request.method == "POST":

        token = request.form.get("csrf_token")
        validar_csrf_token(token)

        # CORES
        cor_principal = (
            request.form.get("cor_principal")
            or "#310505"
        ).strip()

        cor_secundaria = (
            request.form.get("cor_secundaria")
            or "#B89B5E"
        ).strip()

        cor_texto = (
            request.form.get("cor_texto")
            or "#1F1F1F"
        ).strip()

        # VALIDAÇÃO DAS CORES
        padrao_cor = r"^#[0-9A-Fa-f]{6}$"

        if not re.fullmatch(padrao_cor, cor_principal):
            flash("Cor principal inválida.", "erro")
            return redirect(url_for("admin.aparencia"))

        if not re.fullmatch(padrao_cor, cor_secundaria):
            flash("Cor secundária inválida.", "erro")
            return redirect(url_for("admin.aparencia"))

        if not re.fullmatch(padrao_cor, cor_texto):
            flash("Cor do texto inválida.", "erro")
            return redirect(url_for("admin.aparencia"))

        # FONTES
        fonte_titulo = (
            request.form.get("fonte_titulo")
            or "Cormorant Garamond"
        ).strip()

        fonte_texto = (
            request.form.get("fonte_texto")
            or "Montserrat"
        ).strip()

        # LAYOUT
        layout_produtos = (
            request.form.get("layout_produtos")
            or "cards"
        ).strip()

        tamanho_imagem = (
            request.form.get("tamanho_imagem")
            or "medio"
        ).strip()

        # VISIBILIDADE
        mostrar_descricao = (
            1 if request.form.get("mostrar_descricao") else 0
        )

        mostrar_localizacao = (
            1 if request.form.get("mostrar_localizacao") else 0
        )

        mostrar_horarios = (
            1 if request.form.get("mostrar_horarios") else 0
        )

        mostrar_whatsapp = (
            1 if request.form.get("mostrar_whatsapp") else 0
        )

        mostrar_redes_sociais = (
            1 if request.form.get("mostrar_redes_sociais") else 0
        )

        if aparencia_atual is None:

            criar_aparencia(
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

        else:

            atualizar_aparencia(
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

        return redirect(url_for("admin.aparencia"))

    return render_template(
        "admin/aparencia.html",
        usuario=usuario,
        aparencia=aparencia_atual
    )
# QR CODES

@admin.route("/qr-codes")
def qr_codes():

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )

    estabelecimento = buscar_estabelecimento_por_id(
        usuario["estabelecimento_id"]
    )

    return render_template(
        "admin/qr_codes.html",
        usuario=usuario,
        estabelecimento=estabelecimento
    )


@admin.route("/link-cardapio")
def link_cardapio():

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )

    estabelecimento = buscar_estabelecimento_por_id(
        usuario["estabelecimento_id"]
    )

    return render_template(
        "admin/link_cardapio.html",
        usuario=usuario,
        estabelecimento=estabelecimento
    )


# HORÁRIOS
@admin.route(
    "/horarios",
    methods=["GET", "POST"]
)
def horarios():

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )

    estabelecimento_id = usuario["estabelecimento_id"]

 

    if request.method == "POST":
        token = request.form.get("csrf_token")
        validar_csrf_token(token)

        horarios = {}

        # ------------------------------------------------------------

        for dia in range(1, 8):

            periodos = []

            for periodo in range(2):

                abertura = request.form.get(
                    f"horarios[{dia}][{periodo}][abertura]",
                    ""
                ).strip()

                fechamento = request.form.get(
                    f"horarios[{dia}][{periodo}][fechamento]",
                    ""
                ).strip()

                periodos.append({
                    "abertura": abertura,
                    "fechamento": fechamento
                })

            horarios[dia] = periodos

        try:

            salvar_horarios(
                estabelecimento_id,
                horarios
            )

        except ValueError as erro:

            flash(
                str(erro),
                "error"
            )

            return redirect(
                url_for("admin.horarios")
            )

        except Exception:

            flash(
                "Não foi possível salvar os horários.",
                "error"
            )

            return redirect(
                url_for("admin.horarios")
            )

        flash(
            "Horários atualizados com sucesso.",
            "success"
        )

        return redirect(
            url_for("admin.horarios")
        )

   

    horarios_banco = buscar_horarios_por_estabelecimento(
        estabelecimento_id
    )

 
    # 7 DIAS × 2 PERÍODOS
    # ==========================================================

    horarios = {}

    for dia in range(1, 8):

        horarios[dia] = [
            {
                "abertura": "",
                "fechamento": ""
            },
            {
                "abertura": "",
                "fechamento": ""
            }
        ]

    # PREENCHE COM O BANCO

    for horario in horarios_banco:

        dia = int(
            horario["dia_semana"]
        )

        periodo = int(
            horario["periodo"]
        )

        if dia not in horarios:
            continue

        if periodo not in (1, 2):
            continue

        horarios[dia][periodo - 1] = {
            "abertura": horario["hora_abertura"],
            "fechamento": horario["hora_fechamento"]
        }

 

    return render_template(
        "admin/horarios.html",
        usuario=usuario,
        horarios=horarios
    )


@admin.route(
    "/redes-sociais",
    methods=["GET", "POST"]
)
def redes_sociais():

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )

    estabelecimento_id = usuario["estabelecimento_id"]

    # ======================================================
    # BUSCAR REDES EXISTENTES
    # ======================================================

    redes = buscar_redes_sociais_por_estabelecimento(
        estabelecimento_id
    )

    redes_dict = {
        rede["plataforma"]: rede
        for rede in redes
    }

   

    if request.method == "POST":

        token = request.form.get("csrf_token")
        validar_csrf_token(token)

        plataformas = [
            "instagram",
            "facebook",
            "tiktok",
            "youtube",
            "whatsapp"
        ]

        try:

            for plataforma in plataformas:

                url = request.form.get(
                    f"{plataforma}_url",
                    ""
                ).strip()

                if len(url) > LIMITE_URL:
                    flash(
                        f"A URL do {plataforma} é muito longa.",
                        "error"
                    )

                    return redirect(
                        url_for("admin.redes_sociais")
                    )

                ativo = (
                    1
                    if request.form.get(
                        f"{plataforma}_ativo"
                    )
                    else 0
                )

                rede = redes_dict.get(
                    plataforma
                )

                # URL VAZIA

                if not url:

                    if rede:

                        excluir_rede_social(
                            rede["id"],
                            estabelecimento_id
                        )

                    continue

                # VALIDAÇÃO SERVER-SIDE DA URL

                url_analisada = urlparse(
                    url
                )

                if (
                    url_analisada.scheme.lower()
                    not in ("http", "https")
                    or not url_analisada.netloc
                ):
                    flash(
                        f"A URL do {plataforma} é inválida.",
                        "error"
                    )

                    return redirect(
                        url_for("admin.redes_sociais")
                    )

                # CRIAR

                if rede is None:

                    criar_rede_social(
                        estabelecimento_id,
                        plataforma,
                        url
                    )

                # ATUALIZAR

                else:

                    atualizar_rede_social(
                        rede["id"],
                        estabelecimento_id,
                        plataforma,
                        url
                    )

                    alterar_status_rede_social(
                        rede["id"],
                        estabelecimento_id,
                        ativo
                    )


                if rede is None:

                    redes_atualizadas = (
                        buscar_redes_sociais_por_estabelecimento(
                            estabelecimento_id
                        )
                    )

                    for nova_rede in redes_atualizadas:

                        if (
                            nova_rede["plataforma"]
                            == plataforma
                        ):

                            alterar_status_rede_social(
                                nova_rede["id"],
                                estabelecimento_id,
                                ativo
                            )

                            break

        except Exception:

            flash(
                "Não foi possível salvar as redes sociais.",
                "error"
            )

            return redirect(
                url_for("admin.redes_sociais")
            )

        flash(
            "Redes sociais atualizadas com sucesso.",
            "success"
        )

        return redirect(
            url_for("admin.redes_sociais")
        )



    return render_template(
        "admin/redes_sociais.html",
        usuario=usuario,
        redes=redes
    )


@admin.route("/conta", methods=["GET", "POST"])
def conta():

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )

    if request.method == "POST":

        token = request.form.get("csrf_token")

        validar_csrf_token(token)

        nome = (
            request.form.get("nome") or ""
        ).strip()

        email = (
            request.form.get("email") or ""
        ).strip().lower()

        if not nome:
            flash(
                "Informe seu nome.",
                "error"
            )
            return redirect(
                url_for("admin.conta")
            )

        if not email:
            flash(
                "Informe seu e-mail.",
                "error"
            )
            return redirect(
                url_for("admin.conta")
            )

        if not email_valido(email):
            flash("Informe um e-mail válido.", "error")
            return redirect(url_for("admin.conta"))
        
        if len(nome) > LIMITE_NOME_USUARIO:
            flash("O nome é muito longo.", "error")
            return redirect(url_for("admin.conta"))

        if len(email) > LIMITE_EMAIL:
            flash("O e-mail é muito longo.", "error")
            return redirect(url_for("admin.conta"))
        
        try:
            if email == usuario["email"]:
                atualizar_nome(usuario["id"], nome)
                flash("Dados atualizados com sucesso.", "success")
                return redirect(url_for("admin.conta"))

            senha_atual = request.form.get("senha_atual", "")
            usuario_atual = buscar_usuario_por_id(usuario["id"])

            if not senha_atual or not verificar_senha(
                senha_atual,
                usuario_atual["senha"]
            ):
                flash(
                    "Confirme sua senha atual para alterar o e-mail.",
                    "error"
                )
                return redirect(url_for("admin.conta"))

            usuario_existente = buscar_por_email(email)

            if usuario_existente and usuario_existente["id"] != usuario["id"]:
                flash("Este e-mail já está em uso.", "error")
                return redirect(url_for("admin.conta"))

            atualizar_nome(usuario["id"], nome)
            invalidar_tokens_email(usuario["id"])
            token_email = criar_token_email(usuario["id"], email)
            link_confirmacao = url_for(
                "admin.confirmar_email",
                token=token_email,
                _external=True
            )
            enviar_email(
                email,
                "Confirme seu novo e-mail — La Carta",
                "Você solicitou a alteração do e-mail da sua conta La Carta. "
                "Confirme a alteração neste link (válido por 60 minutos):\n\n"
                f"{link_confirmacao}\n\n"
                "Se não foi você, ignore esta mensagem."
            )
            flash(
                "Enviamos um link de confirmação para o novo e-mail.",
                "success"
            )

        except Exception:

            current_app.logger.exception(
                 "Erro ao atualizar conta"
    )

            flash(
                  "Não foi possível atualizar os dados.",
                  "error"
    )

    usuario = usuario_logado()

    return render_template(
        "admin/conta.html",
        usuario=usuario
    )

@admin.route(
    "/confirmar-email/<token>",
    methods=["GET", "POST"]
)
def confirmar_email(token):

    registro = buscar_token_email(token)

    if not token_email_valido(registro):
        flash(
            "Este link de confirmação é inválido ou expirou.",
            "error"
        )
        return redirect(
            url_for("admin.login")
        )

    if buscar_por_email(registro["novo_email"]):
        flash(
            "Este e-mail já está em uso.",
            "error"
        )
        return redirect(
            url_for("admin.login")
        )

    if request.method == "GET":
        return render_template(
            "auth/confirmar_email.html",
            token=token,
            novo_email=registro["novo_email"]
        )

    token_csrf = request.form.get(
        "csrf_token"
    )

    validar_csrf_token(
        token_csrf
    )

    try:

        registro_atual = buscar_token_email(
            token
        )

        if not token_email_valido(
            registro_atual
        ):
            flash(
                "Este link de confirmação é inválido ou expirou.",
                "error"
            )
            return redirect(
                url_for("admin.login")
            )

        token_consumido = marcar_token_email_usado(
            token
        )

        if not token_consumido:
            flash(
                "Este link de confirmação é inválido ou expirou.",
                "error"
            )
            return redirect(
                url_for("admin.login")
            )

        usuario = buscar_usuario_por_id(
            registro_atual["usuario_id"]
        )

        if usuario is None:
            flash(
                "Não foi possível confirmar o novo e-mail.",
                "error"
            )
            return redirect(
                url_for("admin.login")
            )

        if buscar_por_email(
            registro_atual["novo_email"]
        ):
            flash(
                "Este e-mail já está em uso.",
                "error"
            )
            return redirect(
                url_for("admin.login")
            )

        atualizar_email(
            registro_atual["usuario_id"],
            registro_atual["novo_email"]
        )

        try:

            enviar_email(
                usuario["email"],
                "Seu e-mail foi alterado — La Carta",
                "O e-mail de acesso da sua conta foi alterado. "
                "Se não foi você, entre em contato com o suporte imediatamente."
            )

        except Exception:

            current_app.logger.exception(
                "Erro ao enviar AVISO de alteração de Email"
            )

        flash(
            "E-mail alterado e confirmado com sucesso.",
            "success"
        )

    except Exception:

        current_app.logger.exception(
            "Erro ao confirmar Email"
        )

        flash(
            "Não foi possível CONFIRMAR o novo email",
            "error"
        )

    return redirect(
        url_for("admin.login")
    )


@admin.route("/seguranca")
def seguranca():

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )

    return render_template(
        "admin/seguranca.html",
        usuario=usuario
    )
# SUPORTE
@admin.route("/suporte")
def suporte():

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )

    return render_template(
        "admin/suporte.html",
        usuario=usuario
    )



@admin.route(
    "/alterar-senha",
    methods=["GET", "POST"]
)
def alterar_senha():

    usuario = usuario_logado()

    if usuario is None:
        return redirect(
            url_for("admin.login")
        )

    if request.method == "POST":

        token = request.form.get("csrf_token")

        validar_csrf_token(token)

        senha_atual = request.form.get(
            "senha_atual",
            ""
        )

        nova_senha = request.form.get(
            "nova_senha",
            ""
        )

        confirmar_senha = request.form.get(
            "confirmar_senha",
            ""
        )

        if not senha_atual:

            flash(
                "Informe sua senha atual.",
                "error"
            )

            return redirect(
                url_for("admin.alterar_senha")
            )

        if not nova_senha:

            flash(
                "Informe uma nova senha.",
                "error"
            )

            return redirect(
                url_for("admin.alterar_senha")
            )

        if nova_senha != confirmar_senha:

            flash(
                "As senhas não coincidem.",
                "error"
            )

            return redirect(
                url_for("admin.alterar_senha")
            )

        if len(nova_senha) < 8:

            flash(
                "A nova senha deve ter pelo menos 8 caracteres.",
                "error"
            )

            return redirect(
                url_for("admin.alterar_senha")
            )

        usuario_atual = buscar_usuario_por_id(
            usuario["id"]
        )

        if usuario_atual is None:

            session.clear()

            return redirect(
                url_for("admin.login")
            )

        if not verificar_senha(
            senha_atual,
            usuario_atual["senha"]
        ):

            flash(
                "A senha atual está incorreta.",
                "error"
            )

            return redirect(
                url_for("admin.alterar_senha")
            )

        atualizar_senha(
            usuario["id"],
            nova_senha
        )

        invalidar_tokens_recuperacao(usuario["id"])

        usuario_atualizado = buscar_usuario_por_id(
            usuario["id"]
        )

        if (
            usuario_atualizado
            and usuario_atualizado["senha_alterada_em"] is not None
        ):

            session["senha_alterada_em"] = (
                usuario_atualizado[
                    "senha_alterada_em"
                ].isoformat()
            )

        flash(
            "Senha alterada com sucesso.",
            "success"
        )

        return redirect(
            url_for("admin.seguranca")
        )

    return render_template(
        "admin/alterar_senha.html",
        usuario=usuario
    )


@admin.route("/esqueci-senha", methods=["GET", "POST"])
def esqueci_senha():
    if request.method == "POST":
        token = request.form.get("csrf_token")
        validar_csrf_token(token)

        email = request.form.get("email", "").strip().lower()

        if limite_excedido(
            "recuperacao", f"{identificador_cliente()}:{email}", 3, 3600
        ):
            flash(
                "Se houver uma conta com este e-mail, você receberá instruções.",
                "success"
            )
            return redirect(url_for("admin.esqueci_senha"))

        usuario = buscar_por_email(email) if email_valido(email) else None

        if usuario and usuario["ativo"]:
            try:
                invalidar_tokens_recuperacao(usuario["id"])
                token = criar_token_recuperacao(usuario["id"])
                link = url_for(
                    "admin.redefinir_senha",
                    token=token,
                    _external=True
                )
                enviar_email(
                    usuario["email"],
                    "Redefina sua senha — La Carta",
                    "Recebemos uma solicitação para redefinir sua senha. "
                    "Use este link em até 60 minutos:\n\n"
                    f"{link}\n\n"
                    "Se não foi você, ignore esta mensagem."
                )
            except Exception:
                current_app.logger.exception(
                    "Erro ao enviar RECUPERAÇÃO de senha"
                )

        flash(
            "Se houver uma conta com este e-mail, você receberá instruções.",
            "success"
        )
        return redirect(url_for("admin.esqueci_senha"))

    return render_template("auth/esqueci_senha.html")

@admin.route("/redefinir-senha/<token>", methods=["GET", "POST"])
def redefinir_senha(token):

    registro = buscar_token_recuperacao(token)

    if not token_recuperacao_valido(registro):
        flash(
            "Este link é inválido ou expirou. Solicite outro.",
            "error"
        )
        return redirect(
            url_for("admin.esqueci_senha")
        )

    if request.method == "POST":

        token_csrf = request.form.get("csrf_token")
        validar_csrf_token(token_csrf)

        nova_senha = request.form.get(
            "nova_senha",
            ""
        )

        confirmar_senha = request.form.get(
            "confirmar_senha",
            ""
        )

        if len(nova_senha) < 8:
            flash(
                "A nova senha deve ter pelo menos 8 caracteres.",
                "error"
            )

            return render_template(
                "auth/redefinir_senha.html"
            )

        if nova_senha != confirmar_senha:
            flash(
                "As senhas não coincidem.",
                "error"
            )

            return render_template(
                "auth/redefinir_senha.html"
            )

        token_utilizado = marcar_token_recuperacao_usado(
            token
        )

        if not token_utilizado:
            flash(
                "Este link é inválido ou expirou. Solicite outro.",
                "error"
            )

            return redirect(
                url_for("admin.esqueci_senha")
            )

        atualizar_senha(
            registro["usuario_id"],
            nova_senha
        )

        invalidar_tokens_recuperacao(
            registro["usuario_id"]
        )

        session.clear()

        flash(
            "Senha redefinida com sucesso. Entre com sua nova senha.",
            "success"
        )

        return redirect(
            url_for("admin.login")
        )

    return render_template(
        "auth/redefinir_senha.html"
    )
