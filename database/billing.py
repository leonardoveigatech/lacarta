from datetime import date, timedelta

from database.connection import get_connection


def buscar_assinatura(estabelecimento_id):
    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT * FROM assinaturas WHERE estabelecimento_id = %s ORDER BY id DESC LIMIT 1",
            (estabelecimento_id,)
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conexao.close()


def assinatura_bloqueada(estabelecimento_id):
    """Bloqueia a assinatura somente após 4 dias de tolerância.

    Estabelecimentos legados sem assinatura continuam funcionando.
    Assinaturas com status diferente de ativa são bloqueadas.
    """

    assinatura = buscar_assinatura(estabelecimento_id)

    if not assinatura:
        return False

    if str(assinatura.get("status", "")).lower() not in ("ativa", "active"):
        return True

    vencimento = assinatura.get("vencimento")

    if not vencimento:
        return False

    data_limite = vencimento + timedelta(days=4)

    return date.today() > data_limite