import imaplib
import email
from email.header import decode_header
import logging
from typing import List, Dict, Any
from source.ler_emails.config import Config

logger = logging.getLogger(__name__)

class IMAPClient:
    """Cliente IMAP para conexao com caixa de e-mail e leitura de mensagens nao lidas (UNSEEN)."""

    def __init__(self, host: str = None, port: int = None, user: str = None, password: str = None):
        self.host = host if host is not None else Config.IMAP_SERVER
        self.port = port if port is not None else Config.IMAP_PORT
        self.user = user if user is not None else Config.IMAP_USER
        self.password = password if password is not None else Config.IMAP_PASSWORD
        self.connection = None


    def connect(self) -> None:
        """Conecta e realiza login no servidor IMAP SSL."""
        try:
            logger.info(f"Conectando ao servidor IMAP SSL {self.host}:{self.port}...")
            self.connection = imaplib.IMAP4_SSL(self.host, self.port)
            self.connection.login(self.user, self.password)
            logger.info(f"Login IMAP realizado com sucesso para o usuario {self.user}.")
        except Exception as e:
            logger.error(f"Falha ao conectar/autenticar no IMAP ({self.host}): {e}")
            raise

    def disconnect(self) -> None:
        """Encerra a conexao com o servidor IMAP com seguranca."""
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            try:
                self.connection.logout()
            except Exception:
                pass
            logger.info("Conexao IMAP encerrada.")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    @staticmethod
    def decode_mime_header(header_value: str) -> str:
        """Decodifica cabecalhos MIME como Assunto ou Remetente."""
        if not header_value:
            return ""
        decoded_fragments = decode_header(header_value)
        text_parts = []
        for fragment, encoding in decoded_fragments:
            if isinstance(fragment, bytes):
                try:
                    text_parts.append(fragment.decode(encoding or 'utf-8', errors='replace'))
                except Exception:
                    text_parts.append(fragment.decode('latin-1', errors='replace'))
            else:
                text_parts.append(str(fragment))
        return "".join(text_parts)

    def fetch_unread_emails(self, mailbox: str = "INBOX", mark_as_read: bool = False) -> List[Dict[str, Any]]:
        """
        Busca todas as mensagens nao lidas (UNSEEN) na caixa informada.
        
        :param mailbox: Nome da pasta/caixa (padrao: 'INBOX').
        :param mark_as_read: Se True, marca o email como lido no servidor durante o fetch.
        :return: Lista de dicionarios contendo os dados dos e-mails e anexos.
        """
        if not self.connection:
            raise RuntimeError("Cliente IMAP nao esta conectado. Chame connect() primeiro.")

        self.connection.select(mailbox)
        
        status, search_data = self.connection.search(None, "UNSEEN")
        if status != "OK":
            logger.warning(f"Nao foi possivel buscar e-mails nao lidos na pasta {mailbox}.")
            return []

        email_ids = search_data[0].split()
        logger.info(f"Encontrados {len(email_ids)} e-mail(s) nao lido(s) em '{mailbox}'.")

        emails = []
        fetch_cmd = "(RFC822)" if mark_as_read else "(BODY.PEEK[])"

        for mail_id in email_ids:
            try:
                status, data = self.connection.fetch(mail_id, fetch_cmd)
                if status != "OK" or not data:
                    continue

                raw_email = None
                for response_part in data:
                    if isinstance(response_part, tuple):
                        raw_email = response_part[1]
                        break

                if not raw_email:
                    continue

                msg = email.message_from_bytes(raw_email)
                
                subject = self.decode_mime_header(msg.get("Subject", "(Sem Assunto)"))
                sender = self.decode_mime_header(msg.get("From", "(Remetente Desconhecido)"))
                date_str = msg.get("Date", "")
                message_id = msg.get("Message-ID", "")

                body_text = ""
                body_html = ""
                attachments = []

                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))

                        filename = part.get_filename()
                        if filename or "attachment" in content_disposition:
                            if filename:
                                filename = self.decode_mime_header(filename)
                            else:
                                filename = f"anexo_msg_{mail_id.decode()}"

                            file_data = part.get_payload(decode=True)
                            if file_data:
                                attachments.append({
                                    "filename": filename,
                                    "content": file_data,
                                    "content_type": content_type
                                })
                        elif content_type == "text/plain" and "attachment" not in content_disposition:
                            payload = part.get_payload(decode=True)
                            if payload:
                                charset = part.get_content_charset() or 'utf-8'
                                body_text = payload.decode(charset, errors='replace')
                        elif content_type == "text/html" and "attachment" not in content_disposition:
                            payload = part.get_payload(decode=True)
                            if payload:
                                charset = part.get_content_charset() or 'utf-8'
                                body_html = payload.decode(charset, errors='replace')
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        charset = msg.get_content_charset() or 'utf-8'
                        content_type = msg.get_content_type()
                        if content_type == "text/html":
                            body_html = payload.decode(charset, errors='replace')
                        else:
                            body_text = payload.decode(charset, errors='replace')

                emails.append({
                    "id": mail_id.decode(),
                    "message_id": message_id,
                    "subject": subject,
                    "sender": sender,
                    "date": date_str,
                    "body_text": body_text,
                    "body_html": body_html,
                    "attachments": attachments
                })

            except Exception as e:
                logger.error(f"Erro ao processar o e-mail ID {mail_id}: {e}", exc_info=True)

        return emails
