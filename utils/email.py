import smtplib
from email.message import EmailMessage

from config import SMTP_CONFIG


def enviar_email(destinatario, assunto, mensagem):
    """Envia e-mail transacional usando as credenciais SMTP do ambiente."""

    obrigatorios = ("host", "username", "password", "from_email")

    faltantes = [
        campo
        for campo in obrigatorios
        if not SMTP_CONFIG.get(campo)
    ]

    if faltantes:
        raise RuntimeError(
            "Configurações SMTP ausentes: " + ", ".join(faltantes)
        )

    email = EmailMessage()
    email["Subject"] = assunto
    email["From"] = (
        f'{SMTP_CONFIG["from_name"]} '
        f'<{SMTP_CONFIG["from_email"]}>'
    )
    email["To"] = destinatario
    email.set_content(mensagem)

    try:
        with smtplib.SMTP(
            SMTP_CONFIG["host"],
            SMTP_CONFIG["port"],
            timeout=15
        ) as servidor:

            servidor.ehlo()

            if SMTP_CONFIG["use_tls"]:
                servidor.starttls()
                servidor.ehlo()

            servidor.login(
                SMTP_CONFIG["username"],
                SMTP_CONFIG["password"]
            )

            resultado = servidor.send_message(email)

            if resultado:
                raise RuntimeError(
                    "O servidor não aceitou todos os destinatários."
                )

    except Exception as erro:
        print(
            "ERRO NO ENVIO DE E-MAIL:",
            type(erro).__name__,
            str(erro)
        )
        raise