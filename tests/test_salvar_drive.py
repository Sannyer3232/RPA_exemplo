import sys
from pathlib import Path

# Adiciona a raiz do projeto ao sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from tempfile import TemporaryDirectory

from source.salvar_drive.drive_uploader import GoogleDriveUploader
from source.salvar_drive.process_upload import DriveProcessor


# ==========================================
# Testes do GoogleDriveUploader
# ==========================================
def test_uploader_init_defaults():
    uploader = GoogleDriveUploader()
    assert uploader.is_authenticated is False
    assert uploader.drive is None


def test_uploader_authenticate_no_credentials():
    with TemporaryDirectory() as temp_dir:
        fake_secrets = Path(temp_dir) / "non_existent_secrets.json"
        uploader = GoogleDriveUploader(client_secrets_path=str(fake_secrets))
        
        # Como o arquivo não existe, deve retornar False sem lançar erro
        success = uploader.authenticate()
        assert success is False
        assert uploader.is_authenticated is False


@patch("source.salvar_drive.drive_uploader.GoogleAuth")
@patch("source.salvar_drive.drive_uploader.GoogleDrive")
def test_uploader_authenticate_success(mock_drive_cls, mock_gauth_cls):
    with TemporaryDirectory() as temp_dir:
        secrets_file = Path(temp_dir) / "client_secrets.json"
        secrets_file.write_text('{"web": {}}')

        mock_gauth_instance = MagicMock()
        mock_gauth_instance.credentials = MagicMock()
        mock_gauth_instance.access_token_expired = False
        mock_gauth_cls.return_value = mock_gauth_instance

        mock_drive_instance = MagicMock()
        mock_drive_cls.return_value = mock_drive_instance

        uploader = GoogleDriveUploader(client_secrets_path=str(secrets_file))
        success = uploader.authenticate()

        assert success is True
        assert uploader.is_authenticated is True
        assert uploader.drive == mock_drive_instance


def test_uploader_get_or_create_folder_unauthenticated():
    uploader = GoogleDriveUploader()
    folder_id = uploader.get_or_create_folder("MinhaPasta")
    assert folder_id is None


def test_uploader_upload_file_unauthenticated():
    uploader = GoogleDriveUploader()
    with TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "teste.txt"
        test_file.write_text("conteudo")

        success = uploader.upload_file(test_file)
        assert success is False


def test_uploader_upload_file_non_existent_local_file():
    uploader = GoogleDriveUploader()
    uploader.is_authenticated = True
    success = uploader.upload_file(Path("arquivo_que_nao_existe.pdf"))
    assert success is False


@patch("source.salvar_drive.drive_uploader.GoogleDrive")
def test_uploader_get_or_create_folder_existing_and_new(mock_drive_cls):
    mock_drive = MagicMock()
    uploader = GoogleDriveUploader()
    uploader.drive = mock_drive
    uploader.is_authenticated = True

    # 1. Caso existente
    mock_existing_file = {'id': 'folder_123_id'}
    mock_drive.ListFile.return_value.GetList.return_value = [mock_existing_file]

    folder_id_existing = uploader.get_or_create_folder("PastaExistente")
    assert folder_id_existing == 'folder_123_id'

    # 2. Caso não existente -> cria nova pasta
    mock_drive.ListFile.return_value.GetList.return_value = []
    mock_new_folder = MagicMock()
    mock_new_folder.__getitem__.side_effect = lambda key: 'new_folder_999' if key == 'id' else None
    mock_drive.CreateFile.return_value = mock_new_folder

    folder_id_new = uploader.get_or_create_folder("PastaNova")
    assert folder_id_new == 'new_folder_999'


@patch("source.salvar_drive.drive_uploader.GoogleDrive")
def test_uploader_upload_file_create_and_update(mock_drive_cls):
    mock_drive = MagicMock()
    uploader = GoogleDriveUploader()
    uploader.drive = mock_drive
    uploader.is_authenticated = True

    with TemporaryDirectory() as temp_dir:
        sample_file = Path(temp_dir) / "relatorio.pdf"
        sample_file.write_bytes(b"%PDF sample")

        # 1. Novo arquivo
        mock_drive.ListFile.return_value.GetList.return_value = []
        mock_created_file = MagicMock()
        mock_created_file.__getitem__.side_effect = lambda key: 'file_id_new' if key == 'id' else None
        mock_drive.CreateFile.return_value = mock_created_file

        success_new = uploader.upload_file(sample_file, folder_id="folder_abc")
        assert success_new is True
        mock_created_file.SetContentFile.assert_called_once_with(str(sample_file))
        mock_created_file.Upload.assert_called_once()

        # 2. Atualizar arquivo existente
        mock_existing_file = MagicMock()
        mock_existing_file.__getitem__.side_effect = lambda key: 'file_id_existing' if key == 'id' else None
        mock_drive.ListFile.return_value.GetList.return_value = [mock_existing_file]

        success_update = uploader.upload_file(sample_file, folder_id="folder_abc")
        assert success_update is True
        mock_existing_file.SetContentFile.assert_called_with(str(sample_file))


# ==========================================
# Testes do DriveProcessor (Orquestrador)
# ==========================================
def test_drive_processor_unauthenticated_pipeline():
    mock_uploader = MagicMock()
    mock_uploader.authenticate.return_value = False

    processor = DriveProcessor(uploader=mock_uploader)
    stats = processor.run_upload_pipeline()

    assert stats["autenticado"] is False
    assert stats["planilha_enviada"] is False
    assert stats["documentos_enviados"] == 0


def test_drive_processor_authenticated_pipeline():
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        docs_dir = temp_path / "Documentos_OK"
        docs_dir.mkdir()
        (docs_dir / "doc1.pdf").write_bytes(b"pdf1")
        (docs_dir / "doc2.pdf").write_bytes(b"pdf2")

        excel_path = temp_path / "planilha_mestra.xlsx"
        excel_path.write_bytes(b"excel_bytes")

        mock_uploader = MagicMock()
        mock_uploader.authenticate.return_value = True
        mock_uploader.get_or_create_folder.side_effect = lambda name, parent_id=None: f"id_{name}"
        mock_uploader.upload_file.return_value = True

        processor = DriveProcessor(uploader=mock_uploader, docs_dir=docs_dir, excel_path=excel_path)
        stats = processor.run_upload_pipeline()

        assert stats["autenticado"] is True
        assert stats["planilha_enviada"] is True
        assert stats["documentos_enviados"] == 2
        assert stats["falhas_upload"] == 0


if __name__ == "__main__":
    pytest.main(["-v", __file__])
