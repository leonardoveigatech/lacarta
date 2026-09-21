import smtplib
from email.message import EmailMessage

from config import SMTP_CONFIG


def enviar_email(destinatario, assunto, mensagem):
    """Envia e-mail transacional usando as credenciais SMTP do ambiente."""
    obrigatorios = ("host", "username", "password", "from_email")

    if any(not SMTP_CONFIG[campo] for campo in obrigatorios):
        raise RuntimeError("As configurações de e-mail não foram concluídas.")

    email = EmailMessage()
    email["Subject"] = assunto
    email["From"] = f'{SMTP_CONFIG["from_name"]} <{SMTP_CONFIG["from_email"]}>'
    email["To"] = destinatario
    email.set_content(mensagem)

    with smtplib.SMTP(
        SMTP_CONFIG["host"],
        SMTP_CONFIG["port"],
        timeout=15
    ) as servidor:
        if SMTP_CONFIG["use_tls"]:
            servidor.starttls()

        servidor.login(
            SMTP_CONFIG["username"],
            SMTP_CONFIG["password"]
        )
        servidor.send_message(email)
