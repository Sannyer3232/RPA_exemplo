import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Tuple
from source.ler_emails.config import Config

logger = logging.getLogger(__name__)

class SMTPClient:
    """Cliente SMTP para envio de e-mails de retorno, notificacoes e status de processamento."""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        user: str = None,
        password: str = None,
        use_tls: bool = None
    ):
        self.host = host if host is not None else Config.SMTP_SERVER
        self.port = port if port is not None else Config.SMTP_PORT
        self.user = user if user is not None else Config.SMTP_USER
        self.password = password if password is not None else Config.SMTP_PASSWORD
        self.use_tls = use_tls if use_tls is not None else Config.SMTP_USE_TLS


    def send_email(
        self,
        to_address: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        attachments: Optional[List[Tuple[str, bytes]]] = None
    ) -> bool:
        """
        Envia um e-mail utilizando as credenciais SMTP configuradas.

        :param to_address: Endereco de e-mail do destinatario.
        :param subject: Assunto da mensagem.
        :param body_text: Conteudo em texto plano.
        :param body_html: Conteudo HTML (opcional).
        :param attachments: Lista de tuplas (nome_arquivo, bytes_arquivo) opcionais.
        :return: True se enviado com sucesso, False caso contrario.
        """
        if not self.user or not self.password:
            logger.error("Credenciais SMTP nao configuradas no .env. Impossivel enviar e-mail.")
            return False

        try:
            msg = MIMEMultipart("alternative" if not attachments else "mixed")
            msg["From"] = self.user
            msg["To"] = to_address
            msg["Subject"] = subject

            if body_html:
                msg_body = MIMEMultipart("alternative")
                msg_body.attach(MIMEText(body_text, "plain", "utf-8"))
                msg_body.attach(MIMEText(body_html, "html", "utf-8"))
                msg.attach(msg_body)
            else:
                msg.attach(MIMEText(body_text, "plain", "utf-8"))

            if attachments:
                for filename, file_bytes in attachments:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(file_bytes)
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f'attachment; filename="{filename}"'
                    )
                    msg.attach(part)

            logger.info(f"Conectando ao servidor SMTP {self.host}:{self.port}...")
            
            if self.port == 465 and not self.use_tls:
                server = smtplib.SMTP_SSL(self.host, self.port)
            else:
                server = smtplib.SMTP(self.host, self.port)
                if self.use_tls:
                    server.starttls()

            with server:
                server.login(self.user, self.password)
                server.sendmail(self.user, [to_address], msg.as_string())

            logger.info(f"E-mail enviado com sucesso para {to_address} (Assunto: '{subject}').")
            return True

        except Exception as e:
            logger.error(f"Erro ao enviar e-mail via SMTP para {to_address}: {e}", exc_info=True)
            return False
