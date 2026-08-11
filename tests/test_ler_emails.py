import pytest
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from tempfile import TemporaryDirectory

from source.ler_emails.config import Config
from source.ler_emails.file_manager import FileManager
from source.ler_emails.imap_client import IMAPClient
from source.ler_emails.smtp_client import SMTPClient
from source.ler_emails.process_emails import EmailProcessor


# ==========================================
# Testes da Configuração (Config)
# ==========================================
def test_config_validation():
    with patch.object(Config, 'IMAP_USER', 'user@example.com'), \
         patch.object(Config, 'IMAP_PASSWORD', 'secret'):
        assert Config.validate_imap_config() is True

    with patch.object(Config, 'IMAP_USER', ''), \
         patch.object(Config, 'IMAP_PASSWORD', 'secret'):
        assert Config.validate_imap_config() is False

    with patch.object(Config, 'SMTP_USER', 'user@example.com'), \
         patch.object(Config, 'SMTP_PASSWORD', 'secret'):
        assert Config.validate_smtp_config() is True

    with patch.object(Config, 'SMTP_USER', 'user@example.com'), \
         patch.object(Config, 'SMTP_PASSWORD', ''):
        assert Config.validate_smtp_config() is False


# ==========================================
# Testes do FileManager
# ==========================================
def test_file_manager_directories_and_sanitization():
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        with patch.object(Config, 'DIR_DOCUMENTOS_OK', temp_path / "OK"), \
             patch.object(Config, 'DIR_PENDENTES', temp_path / "Pendentes"), \
             patch.object(Config, 'DIR_ARQUIVADOS', temp_path / "Arquivados"):
            
            fm = FileManager()
            assert (temp_path / "OK").exists()
            assert (temp_path / "Pendentes").exists()
            assert (temp_path / "Arquivados").exists()

            # Sanitização
            assert fm.sanitize_filename("relatorio: <vendas>?.pdf") == "relatorio_ _vendas__.pdf"
            assert fm.sanitize_filename("") == "anexo_sem_nome"

            # Categoria
            assert fm.get_target_directory("OK") == temp_path / "OK"
            assert fm.get_target_directory("PENDENTE") == temp_path / "Pendentes"
            assert fm.get_target_directory("ARQUIVADO") == temp_path / "Arquivados"
            assert fm.get_target_directory("UNKNOWN") == temp_path / "Pendentes"


def test_file_manager_save_attachment_and_duplicate_naming():
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        with patch.object(Config, 'DIR_DOCUMENTOS_OK', temp_path / "OK"), \
             patch.object(Config, 'DIR_PENDENTES', temp_path / "Pendentes"), \
             patch.object(Config, 'DIR_ARQUIVADOS', temp_path / "Arquivados"):

            fm = FileManager()
            content = b"Conteudo do PDF"
            filename = "documento.pdf"

            # Salva o primeiro
            path1 = fm.save_attachment(content, filename, category="OK")
            assert path1 is not None
            assert path1.exists()
            assert path1.name == "documento.pdf"

            # Salva o segundo com mesmo nome (deve criar sufixo _1)
            path2 = fm.save_attachment(content, filename, category="OK")
            assert path2 is not None
            assert path2.exists()
            assert path2.name == "documento_1.pdf"


def test_file_manager_save_attachment_exception_handling():
    fm = FileManager()
    with patch("builtins.open", side_effect=OSError("Permissao negada")):
        result = fm.save_attachment(b"test", "test.txt", category="OK")
        assert result is None


# ==========================================
# Testes do IMAPClient
# ==========================================
def test_imap_client_decode_mime_header():
    assert IMAPClient.decode_mime_header("") == ""
    assert IMAPClient.decode_mime_header("Assunto Simples") == "Assunto Simples"
    
    header_utf8 = "=?utf-8?B?UmVsYXTDsnJpbyBkZSBWYW5kYXM=?="
    decoded = IMAPClient.decode_mime_header(header_utf8)
    assert "Relat" in decoded


@patch("imaplib.IMAP4_SSL")
def test_imap_client_connect_and_disconnect(mock_imap):
    mock_instance = MagicMock()
    mock_imap.return_value = mock_instance

    client = IMAPClient(host="imap.fake.com", port=993, user="test@test.com", password="pass")
    client.connect()
    
    mock_imap.assert_called_once_with("imap.fake.com", 993)
    mock_instance.login.assert_called_once_with("test@test.com", "pass")

    client.disconnect()
    mock_instance.close.assert_called_once()
    mock_instance.logout.assert_called_once()


@patch("imaplib.IMAP4_SSL")
def test_imap_client_connect_failure(mock_imap):
    mock_imap.side_effect = Exception("Erro de conexao SSL")
    client = IMAPClient(host="imap.fake.com", user="test@test.com", password="pass")
    with pytest.raises(Exception):
        client.connect()


@patch("imaplib.IMAP4_SSL")
def test_imap_client_context_manager(mock_imap):
    mock_instance = MagicMock()
    mock_imap.return_value = mock_instance

    with IMAPClient(host="imap.fake.com", port=993, user="u", password="p") as client:
        assert client.connection == mock_instance

    mock_instance.logout.assert_called_once()


def test_imap_client_fetch_unread_not_connected():
    client = IMAPClient()
    with pytest.raises(RuntimeError):
        client.fetch_unread_emails()


@patch("imaplib.IMAP4_SSL")
def test_imap_client_fetch_unread_search_failed(mock_imap):
    mock_instance = MagicMock()
    mock_instance.search.return_value = ("NO", [b""])
    mock_imap.return_value = mock_instance

    client = IMAPClient(user="u", password="p")
    client.connect()
    emails = client.fetch_unread_emails()
    assert emails == []


@patch("imaplib.IMAP4_SSL")
def test_imap_client_fetch_unread_emails_parsing(mock_imap):
    mock_instance = MagicMock()
    mock_imap.return_value = mock_instance

    # Criar um e-mail multipart real com anexo
    msg = MIMEMultipart()
    msg["Subject"] = "Relatorio Mensal"
    msg["From"] = "remetente@empresa.com"
    msg["Date"] = "Mon, 10 Aug 2026 10:00:00 -0300"
    msg.attach(MIMEText("Corpo da mensagem em texto", "plain"))

    att = MIMEBase("application", "pdf")
    att.set_payload(b"%PDF-1.4 test content")
    encoders.encode_base64(att)
    att.add_header("Content-Disposition", 'attachment; filename="fatura.pdf"')
    msg.attach(att)

    raw_bytes = msg.as_bytes()

    mock_instance.search.return_value = ("OK", [b"1 2"])
    
    # E-mail 1: mensagem real; E-mail 2: falha no fetch
    mock_instance.fetch.side_effect = [
        ("OK", [(b"1 (RFC822 {1000})", raw_bytes)]),
        ("NO", [])
    ]

    client = IMAPClient(user="u", password="p")
    client.connect()
    emails = client.fetch_unread_emails(mark_as_read=True)

    assert len(emails) == 1
    assert emails[0]["subject"] == "Relatorio Mensal"
    assert emails[0]["sender"] == "remetente@empresa.com"
    assert "Corpo da mensagem em texto" in emails[0]["body_text"]
    assert len(emails[0]["attachments"]) == 1
    assert emails[0]["attachments"][0]["filename"] == "fatura.pdf"
    assert emails[0]["attachments"][0]["content"] == b"%PDF-1.4 test content"


@patch("imaplib.IMAP4_SSL")
def test_imap_client_fetch_single_part_html(mock_imap):
    mock_instance = MagicMock()
    mock_imap.return_value = mock_instance

    msg = MIMEText("<p>Corpo HTML</p>", "html")
    msg["Subject"] = "Informativo HTML"
    msg["From"] = "info@empresa.com"

    mock_instance.search.return_value = ("OK", [b"10"])
    mock_instance.fetch.return_value = ("OK", [(b"10 (BODY.PEEK[])", msg.as_bytes())])

    client = IMAPClient(user="u", password="p")
    client.connect()
    emails = client.fetch_unread_emails(mark_as_read=False)

    assert len(emails) == 1
    assert emails[0]["subject"] == "Informativo HTML"
    assert "<p>Corpo HTML</p>" in emails[0]["body_html"]


# ==========================================
# Testes do SMTPClient
# ==========================================
def test_smtp_client_missing_credentials():
    client = SMTPClient(user="", password="")
    success = client.send_email("dest@test.com", "Subject", "Body")
    assert success is False


@patch("smtplib.SMTP")
def test_smtp_client_send_email_success_tls(mock_smtp):
    mock_server = MagicMock()
    mock_smtp.return_value = mock_server

    client = SMTPClient(host="smtp.test.com", port=587, user="u@test.com", password="p", use_tls=True)
    success = client.send_email(
        to_address="dest@test.com",
        subject="Teste",
        body_text="Texto plano",
        body_html="<h1>HTML</h1>",
        attachments=[("anexo.txt", b"conteudo")]
    )

    assert success is True
    mock_smtp.assert_called_once_with("smtp.test.com", 587)
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("u@test.com", "p")
    mock_server.sendmail.assert_called_once()


@patch("smtplib.SMTP_SSL")
def test_smtp_client_send_email_success_ssl(mock_smtp_ssl):
    mock_server = MagicMock()
    mock_smtp_ssl.return_value = mock_server

    client = SMTPClient(host="smtp.test.com", port=465, user="u@test.com", password="p", use_tls=False)
    success = client.send_email("dest@test.com", "Subject", "Body")

    assert success is True
    mock_smtp_ssl.assert_called_once_with("smtp.test.com", 465)


@patch("smtplib.SMTP")
def test_smtp_client_send_email_exception(mock_smtp):
    mock_smtp.side_effect = Exception("Erro SMTP Server")

    client = SMTPClient(host="smtp.test.com", user="u@test.com", password="p")
    success = client.send_email("dest@test.com", "Subject", "Body")

    assert success is False


# ==========================================
# Testes do EmailProcessor
# ==========================================
def test_email_processor_classification():
    processor = EmailProcessor()
    
    # Validações por extensão
    assert processor.classify_attachment({"subject": "Fatura"}, "fatura.pdf") == "OK"
    assert processor.classify_attachment({"subject": "Documento"}, "contrato.docx") == "OK"
    assert processor.classify_attachment({"subject": "Planilha"}, "dados.xlsx") == "OK"
    assert processor.classify_attachment({"subject": "Executavel"}, "virus.exe") == "PENDENTE"

    # Validações por tags no assunto
    assert processor.classify_attachment({"subject": "[OK] Envio de dados"}, "arquivo.unknown") == "OK"
    assert processor.classify_attachment({"subject": "[PENDENTE] Replicar"}, "documento.pdf") == "PENDENTE"
    assert processor.classify_attachment({"subject": "[ARQUIVAR] Antigo"}, "documento.pdf") == "ARQUIVADO"


@patch("source.ler_emails.process_emails.Config.validate_imap_config", return_value=False)
def test_email_processor_no_imap_config(mock_validate):
    processor = EmailProcessor()
    stats = processor.process_unread_emails()
    assert stats["emails_processados"] == 0


@patch("source.ler_emails.process_emails.Config.validate_imap_config", return_value=True)
@patch("source.ler_emails.process_emails.IMAPClient")
@patch("source.ler_emails.process_emails.SMTPClient")
def test_email_processor_process_unread_emails_flow(mock_smtp_cls, mock_imap_cls, mock_validate):
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        with patch.object(Config, 'DIR_DOCUMENTOS_OK', temp_path / "OK"), \
             patch.object(Config, 'DIR_PENDENTES', temp_path / "Pendentes"), \
             patch.object(Config, 'DIR_ARQUIVADOS', temp_path / "Arquivados"):

            mock_imap_instance = MagicMock()
            mock_imap_cls.return_value.__enter__.return_value = mock_imap_instance
            
            mock_smtp_instance = MagicMock()
            mock_smtp_cls.return_value = mock_smtp_instance

            # Simula dois e-mails: um com anexo PDF e outro sem anexo
            mock_imap_instance.fetch_unread_emails.return_value = [
                {
                    "id": "1",
                    "subject": "Nota Fiscal 101",
                    "sender": "fornecedor@test.com",
                    "date": "2026-08-10",
                    "body_text": "Segue nota fiscal em anexo.",
                    "body_html": "",
                    "attachments": [
                        {"filename": "nf_101.pdf", "content": b"PDF_DATA", "content_type": "application/pdf"}
                    ]
                },
                {
                    "id": "2",
                    "subject": "Dúvida sem anexo",
                    "sender": "cliente@test.com",
                    "date": "2026-08-10",
                    "body_text": "Olá, favor verificar a dúvida.",
                    "body_html": "",
                    "attachments": []
                }
            ]

            processor = EmailProcessor(send_confirmation=True)
            stats = processor.process_unread_emails(mark_as_read=False)

            assert stats["emails_processados"] == 2
            assert stats["anexos_ok"] == 1
            assert stats["emails_sem_anexo"] == 1
            assert (temp_path / "OK" / "nf_101.pdf").exists()
            assert (temp_path / "Pendentes" / "email_sem_anexo_2.txt").exists()
            assert (temp_path / "Arquivados" / "copia_nf_101.pdf").exists()
            assert mock_smtp_instance.send_email.call_count == 2
