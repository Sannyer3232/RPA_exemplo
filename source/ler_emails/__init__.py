"""
Módulo ler_emails: Leitura de e-mails via IMAP, download de anexos,
classificação em pastas (Documentos_OK, Pendentes, Arquivados) e envio SMTP.
"""
from source.ler_emails.config import Config
from source.ler_emails.file_manager import FileManager
from source.ler_emails.imap_client import IMAPClient
from source.ler_emails.smtp_client import SMTPClient
from source.ler_emails.process_emails import EmailProcessor

__all__ = ["Config", "FileManager", "IMAPClient", "SMTPClient", "EmailProcessor"]
