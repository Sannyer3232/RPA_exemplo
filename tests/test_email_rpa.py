import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from source.config import Config
from source.file_manager import FileManager
from source.imap_client import IMAPClient
from source.smtp_client import SMTPClient
from source.process_emails import EmailProcessor

class TestEmailRPA(unittest.TestCase):

    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Override config paths for testing
        Config.DIR_DOCUMENTOS_OK = self.temp_path / "Documentos_OK"
        Config.DIR_PENDENTES = self.temp_path / "Pendentes"
        Config.DIR_ARQUIVADOS = self.temp_path / "Arquivados"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_file_manager_directories_creation(self):
        fm = FileManager()
        self.assertTrue(Config.DIR_DOCUMENTOS_OK.exists())
        self.assertTrue(Config.DIR_PENDENTES.exists())
        self.assertTrue(Config.DIR_ARQUIVADOS.exists())

    def test_sanitize_filename(self):
        raw_filename = 'relatório: "vendas" / 2026?.pdf\r\n'
        sanitized = FileManager.sanitize_filename(raw_filename)
        self.assertNotIn(':', sanitized)
        self.assertNotIn('"', sanitized)
        self.assertNotIn('?', sanitized)
        self.assertTrue(sanitized.endswith(".pdf"))

    def test_save_attachment_ok_and_duplicates(self):
        fm = FileManager()
        content = b"Conteudo do relatorio em PDF"
        filename = "documento.pdf"

        # Save first copy
        path1 = fm.save_attachment(content, filename, category="OK")
        self.assertIsNotNone(path1)
        self.assertTrue(path1.exists())
        self.assertEqual(path1.parent, Config.DIR_DOCUMENTOS_OK)

        # Save second copy with same name (should auto-rename)
        path2 = fm.save_attachment(content, filename, category="OK")
        self.assertIsNotNone(path2)
        self.assertTrue(path2.exists())
        self.assertNotEqual(path1, path2)

    def test_email_processor_classification(self):
        processor = EmailProcessor()
        
        # Valid PDF extension -> OK
        cat_pdf = processor.classify_attachment({"subject": "Nota Fiscal"}, "fatura.pdf")
        self.assertEqual(cat_pdf, "OK")

        # Unknown extension -> PENDENTE
        cat_exe = processor.classify_attachment({"subject": "Arquivo estranho"}, "executavel.exe")
        self.assertEqual(cat_exe, "PENDENTE")

        # Explicit tag in subject [PENDENTE] -> PENDENTE
        cat_tag = processor.classify_attachment({"subject": "[PENDENTE] Replicar dados"}, "documento.pdf")
        self.assertEqual(cat_tag, "PENDENTE")

    def test_decode_mime_header(self):
        header_utf8 = "=?utf-8?B?UmVsYXTDsnJpbyBkZSBWYW5kYXM=?="
        decoded = IMAPClient.decode_mime_header(header_utf8)
        self.assertIn("Relat", decoded)

if __name__ == "__main__":
    unittest.main()
