import os
import calendar
import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort, current_app, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
from database.connection import get_connection
from database.billing import buscar_assinatura, assinatura_bloqueada
from database.usuarios import buscar_por_id as buscar_usuario_por_id
from database.estabelecimentos import buscar_por_id as buscar_estabelecimento_por_id
from config import MAX_UPLOAD_BYTES
import mysql.connector

payments = Blueprint("payments", __name__)
EXTENSOES_COMPROVANTE = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}

def _emv_campo(tag, valor):
    valor = str(valor)
    return f"{tag}{len(valor):02d}{valor}"


def gerar_pix_copia_cola(pix, valor, pagamento_id):
    """Gera payload Pix estático com valor fixo, sem gateway/API de pagamentos."""
    if not pix or not pix.get('chave_pix'):
        return None
    chave = str(pix['chave_pix']).strip()
    nome = re.sub(r'[^A-Za-z0-9 ]', '', str(pix.get('nome_beneficiario') or 'LA CARTA')).strip()[:25] or 'LA CARTA'
    cidade = re.sub(r'[^A-Za-z0-9 ]', '', str(pix.get('cidade_beneficiario') or 'BRASIL')).strip()[:15] or 'BRASIL'
    conta_pix = _emv_campo('00', 'br.gov.bcb.pix') + _emv_campo('01', chave)
    merchant_account = _emv_campo('26', conta_pix)
    valor_formatado = f"{Decimal(str(valor)):.2f}"
    payload = (
        _emv_campo('00', '01') + _emv_campo('01', '12') + merchant_account +
        _emv_campo('52', '0000') + _emv_campo('53', '986') +
        _emv_campo('54', valor_formatado) + _emv_campo('58', 'BR') +
        _emv_campo('59', nome) + _emv_campo('60', cidade) +
        _emv_campo('62', _emv_campo('05', str(pagamento_id)[:25])) + '6304'
    )
    crc = 0xFFFF
    for byte in payload.encode('utf-8'):
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return payload + f"{crc:04X}"



def usuario_atual():
    uid = session.get("usuario_id")
    if not uid:
        return None
    usuario = buscar_usuario_por_id(uid)
    if not usuario or not usuario.get("ativo") or not usuario.get("email_confirmado"):
        session.clear()
        return None
    senha_banco = usuario.get("senha_alterada_em")
    valor_banco = senha_banco.isoformat() if senha_banco else None
    if session.get("senha_alterada_em") != valor_banco:
        session.clear()
        return None
    return usuario


def owner_required(fn):
    """Protege a área do proprietário com uma sessão própria, sem login de cliente."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        owner_email = os.getenv("LA_CARTA_OWNER_EMAIL", "").strip().lower()
        if not owner_email or not os.getenv("LA_CARTA_OWNER_PASSWORD_HASH", "").strip():
            abort(503, description="Configure LA_CARTA_OWNER_EMAIL e LA_CARTA_OWNER_PASSWORD_HASH no .env.")
        if not session.get("proprietario_autenticado") or session.get("proprietario_email") != owner_email:
            return redirect(url_for("payments.login_proprietario"))
        return fn(*args, **kwargs)
    return wrapper


@payments.route("/proprietario/login", methods=["GET", "POST"])
def login_proprietario():
    owner_email = os.getenv("LA_CARTA_OWNER_EMAIL", "").strip().lower()
    password_hash = os.getenv("LA_CARTA_OWNER_PASSWORD_HASH", "").strip()
    if not owner_email or not password_hash:
        abort(503, description="Configure LA_CARTA_OWNER_EMAIL e LA_CARTA_OWNER_PASSWORD_HASH no .env.")

    if session.get("proprietario_autenticado") and session.get("proprietario_email") == owner_email:
        return redirect(url_for("payments.gestao_pagamentos"))

    erro = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        if email == owner_email and check_password_hash(password_hash, senha):
            # Remove apenas a identidade de cliente; não depende de usuario_id.
            for chave in ("usuario_id", "senha_alterada_em", "estabelecimento_id"):
                session.pop(chave, None)
            session["proprietario_autenticado"] = True
            session["proprietario_email"] = owner_email
            session.permanent = True
            return redirect(url_for("payments.gestao_pagamentos"))
        erro = "E-mail ou senha inválidos."

    return render_template("proprietario/loginadm.html", erro=erro)


@payments.route("/proprietario/sair", methods=["POST"])
def logout_proprietario():
    session.pop("proprietario_autenticado", None)
    session.pop("proprietario_email", None)
    return redirect(url_for("payments.login_proprietario"))


def obter_pix():
    conexao = get_connection(); cursor = conexao.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM configuracoes_pix WHERE id = 1 LIMIT 1")
        return cursor.fetchone()
    finally:
        cursor.close(); conexao.close()


def obter_pagamento_aberto(estabelecimento_id, assinatura):
    conexao = get_connection(); cursor = conexao.cursor(dictionary=True)
    try:
        cursor.execute("""SELECT * FROM pagamentos
            WHERE estabelecimento_id=%s AND assinatura_id=%s
              AND status IN ('pendente','comprovante_enviado')
            ORDER BY id DESC LIMIT 1""", (estabelecimento_id, assinatura['id']))
        pagamento = cursor.fetchone()
        if pagamento:
            return pagamento
        cursor.execute("""INSERT INTO pagamentos
            (assinatura_id, estabelecimento_id, descricao, valor, data_emissao, data_vencimento, status, forma_pagamento)
            VALUES (%s,%s,%s,%s,%s,%s,'pendente','pix')""",
            (assinatura['id'], estabelecimento_id, 'Assinatura ' + assinatura['plano'], assinatura.get('valor_total') or assinatura['valor_mensal'], date.today(), assinatura['vencimento']))
        pagamento_id = cursor.lastrowid
        conexao.commit()
        cursor.execute("SELECT * FROM pagamentos WHERE id=%s", (pagamento_id,))
        return cursor.fetchone()
    finally:
        cursor.close(); conexao.close()


def proximo_vencimento(dia, apos=None):
    base = apos or date.today()
    ano, mes = base.year, base.month
    ultimo = calendar.monthrange(ano, mes)[1]
    candidata = date(ano, mes, min(int(dia), ultimo))
    if candidata <= base:
        if mes == 12: ano, mes = ano + 1, 1
        else: mes += 1
        candidata = date(ano, mes, min(int(dia), calendar.monthrange(ano, mes)[1]))
    return candidata


@payments.route('/admin/pagamentos', methods=['GET', 'POST'])
def pagina_cliente():
    usuario = usuario_atual()
    if not usuario:
        return redirect(url_for('admin.login'))
    estabelecimento_id = usuario['estabelecimento_id']
    estabelecimento = buscar_estabelecimento_por_id(estabelecimento_id)
    assinatura = buscar_assinatura(estabelecimento_id)
    pix = obter_pix()
    pagamento = obter_pagamento_aberto(estabelecimento_id, assinatura) if assinatura else None

    if request.method == 'POST':
        if not assinatura or not pagamento:
            flash('Não há uma assinatura disponível para enviar pagamento. Entre em contato com o suporte.', 'error')
            return redirect(url_for('payments.pagina_cliente'))
        nome_pagador = request.form.get('nome_pagador', '').strip()
        observacao = request.form.get('observacao_cliente', '').strip()
        arquivo = request.files.get('comprovante')
        if not nome_pagador:
            flash('Informe o nome de quem realizou o Pix.', 'error')
            return redirect(url_for('payments.pagina_cliente'))
        if not arquivo or not arquivo.filename:
            flash('Anexe o comprovante do Pix.', 'error')
            return redirect(url_for('payments.pagina_cliente'))
        nome_seguro = secure_filename(arquivo.filename)
        ext = os.path.splitext(nome_seguro)[1].lower()
        if ext not in EXTENSOES_COMPROVANTE:
            flash('Formato não permitido. Envie JPG, PNG, WEBP ou PDF.', 'error')
            return redirect(url_for('payments.pagina_cliente'))
        conteudo = arquivo.read(MAX_UPLOAD_BYTES + 1)
        if not conteudo or len(conteudo) > MAX_UPLOAD_BYTES:
            flash('O comprovante deve ter até 5 MB.', 'error')
            return redirect(url_for('payments.pagina_cliente'))
        # Comprovantes ficam fora de static para não serem acessíveis por URL pública.
        pasta = os.path.join(current_app.instance_path, 'uploads', 'comprovantes')
        os.makedirs(pasta, exist_ok=True)
        nome_final = f"pagamento_{pagamento['id']}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}{ext}"
        caminho = os.path.join(pasta, nome_final)
        with open(caminho, 'wb') as f:
            f.write(conteudo)
        conexao = get_connection(); cursor = conexao.cursor()
        try:
            cursor.execute("""UPDATE pagamentos SET nome_pagador=%s, comprovante=%s,
                observacao_cliente=%s, enviado_em=NOW(), status='comprovante_enviado'
                WHERE id=%s AND estabelecimento_id=%s AND status IN ('pendente','comprovante_enviado')""",
                (nome_pagador, 'comprovantes/' + nome_final, observacao or None, pagamento['id'], estabelecimento_id))
            conexao.commit()
        finally:
            cursor.close(); conexao.close()
        flash('Comprovante enviado. A ativação será feita após a conferência manual do pagamento.', 'success')
        return redirect(url_for('payments.pagina_cliente'))

    historico = []
    if assinatura:
        conexao = get_connection(); cursor = conexao.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM pagamentos WHERE estabelecimento_id=%s ORDER BY id DESC LIMIT 12", (estabelecimento_id,))
            historico = cursor.fetchall()
        finally:
            cursor.close(); conexao.close()
    pix_copia_cola = gerar_pix_copia_cola(pix, pagamento['valor'], pagamento['id']) if pix and pagamento and pagamento.get('status') == 'pendente' and pix.get('ativo') else None
    return render_template('admin/pagamentos_cliente.html', usuario=usuario, estabelecimento=estabelecimento,
        assinatura=assinatura, pagamento=pagamento, pix=pix, pix_copia_cola=pix_copia_cola, historico=historico,
        assinatura_atrasada=assinatura_bloqueada(estabelecimento_id))


@payments.route('/gestao-pagamentos/comprovante/<int:pagamento_id>')
@owner_required
def abrir_comprovante(pagamento_id):
    conexao = get_connection(); cursor = conexao.cursor(dictionary=True)
    try:
        cursor.execute("SELECT comprovante FROM pagamentos WHERE id=%s", (pagamento_id,))
        row = cursor.fetchone()
    finally:
        cursor.close(); conexao.close()
    if not row or not row.get('comprovante'):
        abort(404)

    # Compatível com registros antigos: usa somente o nome do arquivo, nunca
    # um caminho fornecido pelo banco, e serve o arquivo apenas após owner_required.
    nome_arquivo = os.path.basename(str(row['comprovante']))
    if not nome_arquivo or nome_arquivo in {'.', '..'}:
        abort(404)
    pasta = os.path.join(current_app.instance_path, 'uploads', 'comprovantes')
    return send_from_directory(pasta, nome_arquivo, as_attachment=False, conditional=True)


@payments.route('/gestao-pagamentos', methods=['GET', 'POST'])
@owner_required
def gestao_pagamentos():
    if request.method == 'POST':
        acao = request.form.get('acao', '')
        conexao = get_connection(); cursor = conexao.cursor(dictionary=True)
        try:
            if acao == 'estabelecimento':
                nome_estabelecimento = request.form.get('nome_estabelecimento', '').strip()
                slug_original = request.form.get('slug', '').strip().lower()
                nome_responsavel = request.form.get('nome_responsavel', '').strip()
                email = request.form.get('email', '').strip().lower()
                senha_inicial = request.form.get('senha_inicial', '')
                descricao = request.form.get('descricao', '').strip() or None
                telefone = request.form.get('telefone', '').strip() or None
                whatsapp = request.form.get('whatsapp', '').strip() or None
                endereco = request.form.get('endereco', '').strip() or None

                slug = unicodedata.normalize('NFKD', slug_original).encode('ascii', 'ignore').decode('ascii')
                slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
                if not nome_estabelecimento or len(nome_estabelecimento) > 100:
                    raise ValueError('Informe um nome de estabelecimento com até 100 caracteres.')
                if not slug or len(slug) > 100:
                    raise ValueError('Informe um endereço curto válido para o cardápio (slug).')
                if not nome_responsavel or len(nome_responsavel) > 100:
                    raise ValueError('Informe o nome do responsável.')
                if not email or len(email) > 255 or '@' not in email:
                    raise ValueError('Informe um e-mail válido para o responsável.')
                if len(senha_inicial) < 8:
                    raise ValueError('A senha inicial deve ter pelo menos 8 caracteres.')

                cursor.execute('SELECT id FROM estabelecimentos WHERE slug=%s', (slug,))
                if cursor.fetchone():
                    raise ValueError('Esse endereço de cardápio já está sendo usado. Escolha outro slug.')
                cursor.execute('SELECT id FROM usuarios WHERE email=%s', (email,))
                if cursor.fetchone():
                    raise ValueError('Já existe uma conta cadastrada com esse e-mail.')

                cursor.execute(
                    '''INSERT INTO estabelecimentos (nome,slug,descricao,telefone,whatsapp,endereco,ativo)
                       VALUES (%s,%s,%s,%s,%s,%s,1)''',
                    (nome_estabelecimento, slug, descricao, telefone, whatsapp, endereco)
                )
                novo_estabelecimento_id = cursor.lastrowid
                cursor.execute(
                    '''INSERT INTO usuarios (estabelecimento_id,nome,email,senha,email_confirmado,ativo)
                       VALUES (%s,%s,%s,%s,1,1)''',
                    (novo_estabelecimento_id, nome_responsavel, email, generate_password_hash(senha_inicial))
                )
                conexao.commit()
                flash(f'Estabelecimento “{nome_estabelecimento}” e acesso do responsável cadastrados. Agora cadastre a assinatura abaixo.', 'success')
            elif acao == 'pix':
                cursor.execute("""INSERT INTO configuracoes_pix
                    (id,chave_pix,tipo_chave,nome_beneficiario,instituicao_financeira,cidade_beneficiario,ativo)
                    VALUES (1,%s,%s,%s,%s,%s,1)
                    ON DUPLICATE KEY UPDATE chave_pix=VALUES(chave_pix), tipo_chave=VALUES(tipo_chave),
                    nome_beneficiario=VALUES(nome_beneficiario), instituicao_financeira=VALUES(instituicao_financeira),
                    cidade_beneficiario=VALUES(cidade_beneficiario), ativo=1""",
                    tuple(request.form.get(k, '').strip() or None for k in ['chave_pix','tipo_chave','nome_beneficiario','instituicao_financeira','cidade_beneficiario']))
                conexao.commit(); flash('Dados Pix salvos.', 'success')
            elif acao == 'assinatura':
                estabelecimento_id = int(request.form.get('estabelecimento_id', '0'))
                plano = request.form.get('plano', '').strip()
                valor = Decimal(request.form.get('valor_mensal', '0'))
                dia = int(request.form.get('dia_vencimento', '21'))
                inicio = date.fromisoformat(request.form.get('data_inicio', date.today().isoformat()))
                vencimento = date.fromisoformat(request.form.get('vencimento', proximo_vencimento(dia).isoformat()))
                status = request.form.get('status', 'ativa')
                if not plano or valor <= 0 or not 1 <= dia <= 28 or status not in ('ativa','inadimplente','suspensa','cancelada'):
                    raise ValueError('Confira plano, valor, dia (1 a 28) e status.')
                cursor.execute('SELECT id FROM estabelecimentos WHERE id=%s', (estabelecimento_id,))
                if not cursor.fetchone(): raise ValueError('Estabelecimento não encontrado.')
                cursor.execute('SELECT id FROM assinaturas WHERE estabelecimento_id=%s ORDER BY id DESC LIMIT 1', (estabelecimento_id,))
                existente = cursor.fetchone()
                if existente:
                    cursor.execute("UPDATE assinaturas SET plano=%s,valor_mensal=%s,dia_vencimento=%s,data_inicio=%s,vencimento=%s,status=%s,observacoes=%s WHERE id=%s",
                        (plano, valor, dia, inicio, vencimento, status, request.form.get('observacoes','').strip() or None, existente['id']))
                    assinatura_id = existente['id']
                else:
                    cursor.execute("INSERT INTO assinaturas (estabelecimento_id,plano,valor_mensal,dia_vencimento,data_inicio,vencimento,status,observacoes) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                        (estabelecimento_id, plano, valor, dia, inicio, vencimento, status, request.form.get('observacoes','').strip() or None))
                    assinatura_id = cursor.lastrowid
                conexao.commit(); flash('Assinatura salva.', 'success')
            elif acao in ('confirmar','rejeitar'):
                pagamento_id = int(request.form.get('pagamento_id','0'))
                cursor.execute("SELECT * FROM pagamentos WHERE id=%s FOR UPDATE", (pagamento_id,))
                pagamento = cursor.fetchone()
                if not pagamento: raise ValueError('Cobrança não encontrada.')
                if acao == 'confirmar':
                    cursor.execute("UPDATE pagamentos SET status='pago',data_pagamento=NOW(),confirmado_por=%s WHERE id=%s", (None, pagamento_id))
                    cursor.execute("SELECT dia_vencimento,vencimento,periodo_meses FROM assinaturas WHERE id=%s FOR UPDATE", (pagamento['assinatura_id'],))
                    row = cursor.fetchone()
                    if row:
                        base_vencimento = row['vencimento'] if row['vencimento'] and row['vencimento'] >= date.today() else date.today()
                        meses = max(1, int(row.get('periodo_meses') or 1))
                        ano = base_vencimento.year + (base_vencimento.month - 1 + meses) // 12
                        mes = (base_vencimento.month - 1 + meses) % 12 + 1
                        venc = date(ano, mes, min(base_vencimento.day, calendar.monthrange(ano, mes)[1]))
                        cursor.execute("UPDATE assinaturas SET status='ativa',vencimento=%s WHERE id=%s", (venc, pagamento['assinatura_id']))
                    flash('Pagamento confirmado e assinatura reativada.', 'success')
                else:
                    cursor.execute("UPDATE pagamentos SET status='rejeitado' WHERE id=%s", (pagamento_id,))
                    flash('Comprovante rejeitado. O cliente poderá enviar outro.', 'warning')
                conexao.commit()
        except (ValueError, InvalidOperation, TypeError, mysql.connector.Error) as e:
            conexao.rollback()
            mensagem = str(e) if isinstance(e, (ValueError, InvalidOperation, TypeError)) else 'Não foi possível salvar. Confira se o e-mail e o endereço do cardápio já estão cadastrados.'
            flash(mensagem or 'Dados inválidos.', 'error')
        finally:
            cursor.close(); conexao.close()
        return redirect(url_for('payments.gestao_pagamentos'))

    conexao = get_connection(); cursor = conexao.cursor(dictionary=True)
    try:
        cursor.execute("""SELECT e.id AS estabelecimento_id,e.nome AS estabelecimento_nome,e.slug,
            a.id AS assinatura_id,a.plano,a.valor_mensal,a.dia_vencimento,a.data_inicio,a.vencimento,a.status AS assinatura_status,a.observacoes AS assinatura_observacoes
            FROM estabelecimentos e LEFT JOIN assinaturas a ON a.id=(SELECT MAX(a2.id) FROM assinaturas a2 WHERE a2.estabelecimento_id=e.id)
            ORDER BY e.nome""")
        estabelecimentos = cursor.fetchall()
        cursor.execute("""SELECT p.*,e.nome AS estabelecimento_nome FROM pagamentos p
            JOIN estabelecimentos e ON e.id=p.estabelecimento_id ORDER BY
            CASE WHEN p.status='comprovante_enviado' THEN 0 WHEN p.status='pendente' THEN 1 ELSE 2 END,
            p.id DESC LIMIT 100""")
        pagamentos = cursor.fetchall()
    finally:
        cursor.close(); conexao.close()
    pix = obter_pix()
    return render_template('proprietario/gestao_pagamentos.html', estabelecimentos=estabelecimentos, pagamentos=pagamentos, pix=pix, today=date.today().isoformat())