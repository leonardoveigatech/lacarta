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
from utils.email import enviar_email
from utils.csrf import validar_csrf_token


from database.connection import get_connection
from database.usuarios import buscar_por_email

from database.email_confirmation import (
    criar_token as criar_token_confirmacao,
    buscar_token as buscar_token_confirmacao,
    marcar_como_usado as marcar_token_confirmacao_usado,
    invalidar_tokens_usuario as invalidar_tokens_confirmacao
)

from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

from PIL import Image, UnidentifiedImageError

from config import MAX_UPLOAD_BYTES, MAX_IMAGE_PIXELS

import os
import re
import unicodedata

from datetime import datetime


auth = Blueprint("auth", __name__)


# ============================================================
# CONFIGURAÇÕES
# ============================================================

DIAS_VALIDOS = {
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7"
}


EXTENSOES_PERMITIDAS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}


LIMITE_NOME_USUARIO = 100
LIMITE_EMAIL = 254
LIMITE_NOME_ESTABELECIMENTO = 100
LIMITE_DESCRICAO_ESTABELECIMENTO = 1000
LIMITE_TELEFONE = 30
LIMITE_WHATSAPP = 30
LIMITE_CEP = 20
LIMITE_ESTADO = 50
LIMITE_CIDADE = 100
LIMITE_BAIRRO = 100
LIMITE_RUA = 150
LIMITE_NUMERO = 20
LIMITE_COMPLEMENTO = 100


# ============================================================
# SLUG
# ============================================================

def gerar_slug(nome):
    texto = unicodedata.normalize(
        "NFKD",
        nome
    ).encode(
        "ascii",
        "ignore"
    ).decode("ascii")

    texto = texto.lower()

    texto = re.sub(
        r"[^a-z0-9]+",
        "-",
        texto
    )

    texto = texto.strip("-")

    return texto


def slug_disponivel(cursor, slug):
    cursor.execute(
        """
        SELECT id
        FROM estabelecimentos
        WHERE slug = %s
        LIMIT 1
        """,
        (slug,)
    )

    return cursor.fetchone() is None


def gerar_slug_unico(cursor, nome):
    slug_base = gerar_slug(nome)

    if not slug_base:
        slug_base = "estabelecimento"

    slug = slug_base
    contador = 2

    while not slug_disponivel(cursor, slug):
        slug = f"{slug_base}-{contador}"
        contador += 1

    return slug


# ============================================================
# UPLOAD DE IMAGENS
# ============================================================

def imagem_valida(arquivo, extensao):
    """
    Verifica a assinatura real do arquivo para evitar que
    arquivos não-imagem sejam enviados apenas com uma extensão
    permitida.
    """

    formatos = {
        ".jpg": "JPEG",
        ".jpeg": "JPEG",
        ".png": "PNG",
        ".webp": "WEBP"
    }

    try:
        arquivo.stream.seek(0, 2)

        if arquivo.stream.tell() > MAX_UPLOAD_BYTES:
            return False

        arquivo.stream.seek(0)

        imagem = Image.open(
            arquivo.stream
        )

        if imagem.format != formatos[extensao]:
            return False

        if imagem.width * imagem.height > MAX_IMAGE_PIXELS:
            return False

        imagem.verify()

        arquivo.stream.seek(0)

        return True

    except (
        UnidentifiedImageError,
        OSError,
        ValueError
    ):
        return False


def salvar_imagem(arquivo, pasta):

    if not arquivo or not arquivo.filename:
        return None

    nome_seguro = secure_filename(
        arquivo.filename
    )

    if not nome_seguro:
        raise ValueError(
            "Nome de arquivo inválido."
        )

    extensao = os.path.splitext(
        nome_seguro
    )[1].lower()

    if extensao not in EXTENSOES_PERMITIDAS:
        raise ValueError(
            "Formato de imagem não permitido."
        )

    if not imagem_valida(
        arquivo,
        extensao
    ):
        raise ValueError(
            "O arquivo enviado não é uma imagem válida."
        )

    nome_final = (
        f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        f"{extensao}"
    )

    pasta_completa = os.path.join(
        "static",
        "uploads",
        pasta
    )

    os.makedirs(
        pasta_completa,
        exist_ok=True
    )

    caminho_completo = os.path.join(
        pasta_completa,
        nome_final
    )

    arquivo.save(
        caminho_completo
    )

    return os.path.join(
        "uploads",
        pasta,
        nome_final
    ).replace("\\", "/")


# ============================================================
# ENDEREÇO
# ============================================================

def montar_endereco(form):
    partes = []

    cep = form.get(
        "cep",
        ""
    ).strip()

    estado = form.get(
        "estado",
        ""
    ).strip()

    cidade = form.get(
        "cidade",
        ""
    ).strip()

    bairro = form.get(
        "bairro",
        ""
    ).strip()

    rua = form.get(
        "rua",
        ""
    ).strip()

    numero = form.get(
        "numero",
        ""
    ).strip()

    complemento = form.get(
        "complemento",
        ""
    ).strip()

    if rua:
        endereco_rua = rua

        if numero:
            endereco_rua += f", {numero}"

        partes.append(
            endereco_rua
        )

    if complemento:
        partes.append(
            complemento
        )

    if bairro:
        partes.append(
            bairro
        )

    if cidade:
        partes.append(
            cidade
        )

    if estado:
        partes.append(
            estado.upper()
        )

    if cep:
        partes.append(
            f"CEP {cep}"
        )

    return ", ".join(partes)


# ============================================================
# VALIDAÇÃO DE HORÁRIOS
# ============================================================

def horario_valido(horario):
    """
    Aceita horários no formato HH:MM.
    """

    if not horario:
        return False

    if not re.fullmatch(
        r"([01]\d|2[0-3]):[0-5]\d",
        horario
    ):
        return False

    return True


def validar_horarios(form):
    dias = form.getlist(
        "dias_funcionamento"
    )

    if not dias:
        return (
            False,
            "Selecione pelo menos um dia de funcionamento."
        )

    for dia in dias:

        if dia not in DIAS_VALIDOS:
            return (
                False,
                "Dia de funcionamento inválido."
            )

        abertura_1 = form.get(
            f"horarios[{dia}][0][abertura]",
            ""
        ).strip()

        fechamento_1 = form.get(
            f"horarios[{dia}][0][fechamento]",
            ""
        ).strip()

        if not abertura_1 or not fechamento_1:
            return (
                False,
                "Informe abertura e fechamento "
                f"para o dia {dia}."
            )

        if not horario_valido(abertura_1):
            return (
                False,
                "O horário de abertura "
                f"do dia {dia} é inválido."
            )

        if not horario_valido(fechamento_1):
            return (
                False,
                "O horário de fechamento "
                f"do dia {dia} é inválido."
            )

        if fechamento_1 <= abertura_1:
            return (
                False,
                "O horário de fechamento deve "
                "ser posterior ao horário de abertura."
            )

        abertura_2 = form.get(
            f"horarios[{dia}][1][abertura]",
            ""
        ).strip()

        fechamento_2 = form.get(
            f"horarios[{dia}][1][fechamento]",
            ""
        ).strip()

        if abertura_2 or fechamento_2:

            if not abertura_2 or not fechamento_2:
                return (
                    False,
                    "Preencha abertura e fechamento "
                    "do segundo período."
                )

            if not horario_valido(abertura_2):
                return (
                    False,
                    "O horário de abertura "
                    f"do segundo período do dia {dia} é inválido."
                )

            if not horario_valido(fechamento_2):
                return (
                    False,
                    "O horário de fechamento "
                    f"do segundo período do dia {dia} é inválido."
                )

            if fechamento_2 <= abertura_2:
                return (
                    False,
                    "O fechamento do segundo período "
                    "deve ser posterior à abertura."
                )

            if abertura_2 < fechamento_1:
                return (
                    False,
                    "O segundo período não pode começar "
                    "antes do término do primeiro período."
                )

    return True, None


# ============================================================
# CADASTRO
# ============================================================

@auth.route(
    "/cadastro",
    methods=["GET", "POST"]
)
def cadastro():

    if request.method == "GET":
        return render_template(
            "auth/cadastro.html"
        )

    if limite_excedido(
        "cadastro",
        identificador_cliente(),
        5,
        3600
    ):
        return "Muitas tentativas de cadastro. Tente novamente mais tarde.", 429

    nome = request.form.get(
        "nome",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    senha = request.form.get(
        "senha",
        ""
    )

    confirmar_senha = request.form.get(
        "confirmarSenha",
        ""
    )

    nome_estabelecimento = request.form.get(
        "nomeEstabelecimento",
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

    termos = request.form.get(
        "termos"
    )

    # --------------------------------------------------------
    # VALIDAÇÕES BÁSICAS
    # --------------------------------------------------------

    if not nome:
        return render_template(
            "auth/cadastro.html",
            erro="Informe seu nome."
        )

    if not email:
        return render_template(
            "auth/cadastro.html",
            erro="Informe seu e-mail."
        )

    if not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+",
        email
    ):
        return render_template(
            "auth/cadastro.html",
            erro="Informe um e-mail válido."
        )

    if not senha or len(senha) < 8:
        return render_template(
            "auth/cadastro.html",
            erro="A senha deve ter pelo menos 8 caracteres."
        )

    if senha != confirmar_senha:
        return render_template(
            "auth/cadastro.html",
            erro="As senhas não coincidem."
        )

    if not termos:
        return render_template(
            "auth/cadastro.html",
            erro="Você precisa aceitar os termos."
        )

    if not nome_estabelecimento:
        return render_template(
            "auth/cadastro.html",
            erro="Informe o nome do estabelecimento."
        )

    if len(nome) > LIMITE_NOME_USUARIO:
        return render_template(
            "auth/cadastro.html",
            erro="O nome é muito longo."
        )

    if len(email) > LIMITE_EMAIL:
        return render_template(
            "auth/cadastro.html",
            erro="O e-mail é muito longo."
        )

    if len(nome_estabelecimento) > LIMITE_NOME_ESTABELECIMENTO:
        return render_template(
            "auth/cadastro.html",
            erro="O nome do estabelecimento é muito longo."
        )

    if len(descricao) > LIMITE_DESCRICAO_ESTABELECIMENTO:
        return render_template(
            "auth/cadastro.html",
            erro="A descrição do estabelecimento é muito longa."
        )

    if len(telefone) > LIMITE_TELEFONE:
        return render_template(
            "auth/cadastro.html",
            erro="O telefone é muito longo."
        )

    if len(whatsapp) > LIMITE_WHATSAPP:
        return render_template(
            "auth/cadastro.html",
            erro="O WhatsApp é muito longo."
        )

    if buscar_por_email(email):
        return render_template(
            "auth/cadastro.html",
            erro="Este e-mail já está cadastrado."
        )

    # --------------------------------------------------------
    # VALIDAÇÃO DOS HORÁRIOS
    # --------------------------------------------------------

    horarios_validos, erro_horarios = validar_horarios(
        request.form
    )

    if not horarios_validos:
        return render_template(
            "auth/cadastro.html",
            erro=erro_horarios
        )

    # --------------------------------------------------------
    # ENDEREÇO
    # --------------------------------------------------------

    cep = request.form.get("cep", "").strip()
    estado = request.form.get("estado", "").strip()
    cidade = request.form.get("cidade", "").strip()
    bairro = request.form.get("bairro", "").strip()
    rua = request.form.get("rua", "").strip()
    numero = request.form.get("numero", "").strip()
    complemento = request.form.get("complemento", "").strip()

    if len(cep) > LIMITE_CEP:
        return render_template(
            "auth/cadastro.html",
            erro="Limite de caracteres excedido"
        )

    if len(estado) > LIMITE_ESTADO:
        return render_template(
            "auth/cadastro.html",
            erro="Limite de caracteres excedido."
        )

    if len(cidade) > LIMITE_CIDADE:
        return render_template(
            "auth/cadastro.html",
            erro="Limite de caracteres excedido."
        )

    if len(bairro) > LIMITE_BAIRRO:
        return render_template(
            "auth/cadastro.html",
            erro="Limite de caracteres excedido."
        )

    if len(rua) > LIMITE_RUA:
        return render_template(
            "auth/cadastro.html",
            erro="Limite de caracteres excedido."
        )

    if len(numero) > LIMITE_NUMERO:
        return render_template(
            "auth/cadastro.html",
            erro="Limite de caracteres excedido."
        )

    if len(complemento) > LIMITE_COMPLEMENTO:
        return render_template(
            "auth/cadastro.html",
            erro="Limite de caracteres excedido."
        )

    endereco = montar_endereco(
        request.form
    )

    conexao = None
    cursor = None

    arquivos_salvos = []

    try:

        # ----------------------------------------------------
        # TRANSAÇÃO
        # ----------------------------------------------------

        conexao = get_connection()
        conexao.start_transaction()

        cursor = conexao.cursor()

        # ----------------------------------------------------
        # SLUG
        # ----------------------------------------------------

        slug = gerar_slug_unico(
            cursor,
            nome_estabelecimento
        )

        # ----------------------------------------------------
        # LOGO
        # ----------------------------------------------------

        logo = salvar_imagem(
            request.files.get("logo"),
            "logos"
        )

        if logo:
            arquivos_salvos.append(
                logo
            )

        # ----------------------------------------------------
        # IMAGEM DE CAPA
        # ----------------------------------------------------

        imagem_capa = salvar_imagem(
            request.files.get("imagemCapa"),
            "capas"
        )

        if imagem_capa:
            arquivos_salvos.append(
                imagem_capa
            )

        # ----------------------------------------------------
        # ESTABELECIMENTO
        # ----------------------------------------------------

        cursor.execute(
            """
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
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
            """,
            (
                nome_estabelecimento,
                slug,
                logo,
                imagem_capa,
                descricao or None,
                telefone or None,
                whatsapp or None,
                endereco or None
            )
        )

        estabelecimento_id = cursor.lastrowid

        # ----------------------------------------------------
        # USUÁRIO
        # ----------------------------------------------------

        senha_hash = generate_password_hash(
            senha
        )

        cursor.execute(
            """
            INSERT INTO usuarios (
                estabelecimento_id,
                nome,
                email,
                senha,
                email_confirmado
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                estabelecimento_id,
                nome,
                email,
                senha_hash,
                0
            )
        )

        usuario_id = cursor.lastrowid

        # ----------------------------------------------------
        # HORÁRIOS
        # ----------------------------------------------------

        dias = request.form.getlist(
            "dias_funcionamento"
        )

        for dia in dias:

            abertura_1 = request.form.get(
                f"horarios[{dia}][0][abertura]",
                ""
            ).strip()

            fechamento_1 = request.form.get(
                f"horarios[{dia}][0][fechamento]",
                ""
            ).strip()

            cursor.execute(
                """
                INSERT INTO horarios_funcionamento (
                    estabelecimento_id,
                    dia_semana,
                    periodo,
                    hora_abertura,
                    hora_fechamento
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    estabelecimento_id,
                    int(dia),
                    1,
                    abertura_1,
                    fechamento_1
                )
            )

            abertura_2 = request.form.get(
                f"horarios[{dia}][1][abertura]",
                ""
            ).strip()

            fechamento_2 = request.form.get(
                f"horarios[{dia}][1][fechamento]",
                ""
            ).strip()

            if abertura_2 and fechamento_2:

                cursor.execute(
                    """
                    INSERT INTO horarios_funcionamento (
                        estabelecimento_id,
                        dia_semana,
                        periodo,
                        hora_abertura,
                        hora_fechamento
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        estabelecimento_id,
                        int(dia),
                        2,
                        abertura_2,
                        fechamento_2
                    )
                )

        # ----------------------------------------------------
        # FINALIZA TRANSAÇÃO
        # ----------------------------------------------------

        conexao.commit()

        # ----------------------------------------------------
        # INVALIDA TOKENS ANTERIORES
        # ----------------------------------------------------

        invalidar_tokens_confirmacao(
            usuario_id
        )

        # ----------------------------------------------------
        # GERA TOKEN DE CONFIRMAÇÃO
        # ----------------------------------------------------

        token_confirmacao = criar_token_confirmacao(
            usuario_id
        )

        link_confirmacao = url_for(
            "auth.confirmar_cadastro",
            token=token_confirmacao,
            _external=True
        )

        # ----------------------------------------------------
        # ENVIA E-MAIL
        # ----------------------------------------------------

        try:

            enviar_email(
                email,
                "Confirme seu e-mail — La Carta",
                "Seu cadastro no La Carta foi criado com sucesso.\n\n"
                "Para ativar sua conta, confirme seu endereço de e-mail "
                "clicando no link abaixo.\n\n"
                f"{link_confirmacao}\n\n"
                "Este link é válido por 60 minutos.\n\n"
                "Se você não realizou este cadastro, ignore esta mensagem."
            )

        except Exception as erro:

            return render_template(
                "auth/cadastro.html",
                erro=(
                    "Seu cadastro foi criado, mas não foi possível "
                    "enviar o e-mail de confirmação. "
                    "Entre em contato com o suporte."
                )
            )

        # ----------------------------------------------------
        # NÃO CRIA SESSÃO
        # ----------------------------------------------------

        session.clear()

        return render_template(
            "auth/cadastro_sucesso.html",
            email=email
        )

    # --------------------------------------------------------
    # ERRO
    # --------------------------------------------------------

    except Exception as erro:

        if conexao:
            conexao.rollback()

        for caminho in arquivos_salvos:

            caminho_completo = os.path.join(
                "static",
                caminho
            )

            if os.path.exists(
                caminho_completo
            ):
                try:
                    os.remove(
                        caminho_completo
                    )
                except OSError:
                    pass

        return render_template(
            "auth/cadastro.html",
            erro=(
                "Não foi possível concluir o cadastro. "
                "Tente novamente."
            )
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()
# ============================================================
# CONFIRMAÇÃO DO CADASTRO
# ============================================================
@auth.route(
    "/confirmar-cadastro/<token>",
    methods=["GET", "POST"]
)
def confirmar_cadastro(token):

    registro = buscar_token_confirmacao(
        token
    )

    if registro is None:
        return render_template(
            "auth/confirmacao_email.html",
            sucesso=False,
            mensagem="Este link de confirmação é inválido."
        )

    if registro["usado"]:
        return render_template(
            "auth/confirmacao_email.html",
            sucesso=False,
            mensagem="Este link de confirmação já foi utilizado."
        )

    if registro["expira_em"] < datetime.now():
        return render_template(
            "auth/confirmacao_email.html",
            sucesso=False,
            mensagem="Este link de confirmação expirou."
        )

    # --------------------------------------------------------
    # ABERTURA DO LINK
    # --------------------------------------------------------

    if request.method == "GET":

        return render_template(
            "auth/confirmacao_email.html",
            sucesso=None,
            mensagem=None
        )

    # --------------------------------------------------------
    # CONFIRMAÇÃO
    # --------------------------------------------------------

    token_csrf = request.form.get(
        "csrf_token"
    )

    validar_csrf_token(
        token_csrf
    )

    conexao = None
    cursor = None

    try:

        conexao = get_connection()
        cursor = conexao.cursor()

        # ----------------------------------------------------
        # CONFERE NOVAMENTE O USUÁRIO
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                id,
                email_confirmado
            FROM usuarios
            WHERE id = %s
            LIMIT 1
            """,
            (
                registro["usuario_id"],
            )
        )

        usuario = cursor.fetchone()

        if usuario is None:

            return render_template(
                "auth/confirmacao_email.html",
                sucesso=False,
                mensagem="Usuário não encontrado."
            )

        # ----------------------------------------------------
        # JÁ CONFIRMADO
        # ----------------------------------------------------

        if usuario[1]:

            conexao.rollback()

            marcar_token_confirmacao_usado(
                registro["id"]
            )

            return render_template(
                "auth/confirmacao_email.html",
                sucesso=True,
                mensagem=(
                    "Seu e-mail já estava confirmado. "
                    "Agora você já pode entrar na sua conta."
                )
            )

        # ----------------------------------------------------
        # CONFIRMA E-MAIL
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE usuarios
            SET email_confirmado = 1
            WHERE id = %s
              AND email_confirmado = 0
            """,
            (
                registro["usuario_id"],
            )
        )

        if cursor.rowcount != 1:

            conexao.rollback()

            return render_template(
                "auth/confirmacao_email.html",
                sucesso=False,
                mensagem=(
                    "Não foi possível confirmar seu e-mail. "
                    "Tente novamente."
                )
            )

        conexao.commit()

        # ----------------------------------------------------
        # INVALIDA O TOKEN
        # ----------------------------------------------------

        marcar_token_confirmacao_usado(
            registro["id"]
        )

        # ----------------------------------------------------
        # SUCESSO
        # ----------------------------------------------------

        return render_template(
            "auth/confirmacao_email.html",
            sucesso=True,
            mensagem=(
                "Seu e-mail foi confirmado com sucesso. "
                "Agora você já pode entrar na sua conta."
            )
        )

    except Exception:

        if conexao:
            conexao.rollback()

        current_app.logger.exception(
            "Erro ao confirmar Email"
        )

        return render_template(
            "auth/confirmacao_email.html",
            sucesso=False,
            mensagem=(
                "Não foi possível confirmar seu e-mail. "
                "Tente novamente."
            )
        )

    finally:

        if cursor:
            cursor.close()

        if conexao:
            conexao.close()