import os
import logging
from pathlib import Path
from typing import Optional

try:
    from pydrive2.auth import GoogleAuth
    from pydrive2.drive import GoogleDrive
except ImportError:
    GoogleAuth = None
    GoogleDrive = None

logger = logging.getLogger(__name__)

class GoogleDriveUploader:
    """Cliente wrapper para autenticação e upload de arquivos no Google Drive via PyDrive2."""

    def __init__(
        self,
        client_secrets_path: Optional[str] = None,
        settings_path: Optional[str] = None,
        root_folder_id: Optional[str] = None
    ):
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.secrets_path = Path(client_secrets_path or os.getenv("GOOGLE_DRIVE_CLIENT_SECRETS_PATH", base_dir / "client_secrets.json"))
        self.settings_path = Path(settings_path or os.getenv("GOOGLE_DRIVE_SETTINGS_PATH", base_dir / "settings.yaml"))
        self.root_folder_id = root_folder_id or os.getenv("GOOGLE_DRIVE_FOLDER_ID", "").strip() or None

        self.gauth = None
        self.drive = None
        self.is_authenticated = False

    def authenticate(self) -> bool:
        """
        Autentica no Google Drive usando PyDrive2.
        
        :return: True se autenticado com sucesso, False caso contrário.
        """
        if GoogleAuth is None or GoogleDrive is None:
            logger.error("Biblioteca PyDrive2 não está instalada.")
            return False

        try:
            self.gauth = GoogleAuth(settings_file=str(self.settings_path) if self.settings_path.exists() else None)
            
            # Se secrets file existir, define no gauth
            if self.secrets_path.exists():
                self.gauth.settings['client_config_backend'] = 'file'
                self.gauth.settings['client_config_file'] = str(self.secrets_path)

            # Tenta carregar credenciais salvas
            creds_file = self.secrets_path.parent / "mycreds.txt"
            if creds_file.exists():
                self.gauth.LoadCredentialsFile(str(creds_file))

            if self.gauth.credentials is None:
                # Tenta autenticação via webserver local se houver client_secrets.json
                if self.secrets_path.exists():
                    logger.info("Iniciando autenticação via servidor web local do Google Drive...")
                    self.gauth.LocalWebserverAuth()
                else:
                    logger.warning(
                        f"Arquivo de credenciais 'client_secrets.json' não foi encontrado em '{self.secrets_path}'. "
                        "Upload para o Google Drive será ignorado."
                    )
                    return False
            elif self.gauth.access_token_expired:
                self.gauth.Refresh()
            else:
                self.gauth.Authorize()

            # Salva credenciais renovadas
            if self.gauth.credentials:
                self.gauth.SaveCredentialsFile(str(creds_file))

            self.drive = GoogleDrive(self.gauth)
            self.is_authenticated = True
            logger.info("Autenticação com o Google Drive realizada com sucesso!")
            return True

        except Exception as e:
            logger.error(f"Falha na autenticação do Google Drive: {e}", exc_info=True)
            self.is_authenticated = False
            return False

    def get_or_create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """
        Busca uma pasta remota no Google Drive pelo nome. Se não existir, cria a pasta.

        :param folder_name: Nome da pasta no Google Drive.
        :param parent_id: ID da pasta pai (opcional).
        :return: ID da pasta encontrada/criada ou None.
        """
        if not self.is_authenticated or not self.drive:
            logger.warning("Google Drive não está autenticado. Impossível buscar/criar pasta.")
            return None

        target_parent = parent_id or self.root_folder_id
        try:
            # Constrói query de busca por pasta
            query = f"title = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            if target_parent:
                query += f" and '{target_parent}' in parents"

            file_list = self.drive.ListFile({'q': query}).GetList()
            if file_list:
                folder_id = file_list[0]['id']
                logger.info(f"Pasta remota '{folder_name}' encontrada no Google Drive (ID: {folder_id}).")
                return folder_id

            # Cria nova pasta se não existir
            folder_metadata = {
                'title': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if target_parent:
                folder_metadata['parents'] = [{'id': target_parent}]

            folder = self.drive.CreateFile(folder_metadata)
            folder.Upload()
            logger.info(f"Nova pasta remota '{folder_name}' criada no Google Drive (ID: {folder['id']}).")
            return folder['id']

        except Exception as e:
            logger.error(f"Erro ao buscar/criar pasta '{folder_name}' no Google Drive: {e}", exc_info=True)
            return None

    def upload_file(
        self,
        file_path: Path,
        folder_id: Optional[str] = None,
        remote_title: Optional[str] = None
    ) -> bool:
        """
        Faz o upload de um arquivo local para o Google Drive (atualiza se já existir).

        :param file_path: Path do arquivo local.
        :param folder_id: ID da pasta remota de destino (opcional).
        :param remote_title: Nome do arquivo no Google Drive (padrão: nome original).
        :return: True se enviado com sucesso, False caso contrário.
        """
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            logger.error(f"Arquivo local para upload não existe: {file_path}")
            return False

        if not self.is_authenticated or not self.drive:
            logger.warning(f"Google Drive não autenticado. Upload do arquivo '{path.name}' cancelado.")
            return False

        title = remote_title or path.name
        target_parent = folder_id or self.root_folder_id

        try:
            # Verifica se arquivo já existe no destino para atualizar
            query = f"title = '{title}' and trashed = false"
            if target_parent:
                query += f" and '{target_parent}' in parents"

            existing_files = self.drive.ListFile({'q': query}).GetList()
            if existing_files:
                drive_file = existing_files[0]
                logger.info(f"Atualizando arquivo existente '{title}' no Google Drive (ID: {drive_file['id']})...")
            else:
                meta = {'title': title}
                if target_parent:
                    meta['parents'] = [{'id': target_parent}]
                drive_file = self.drive.CreateFile(meta)
                logger.info(f"Criando novo arquivo '{title}' no Google Drive...")

            drive_file.SetContentFile(str(path))
            drive_file.Upload()

            logger.info(f"Upload de '{path.name}' para o Google Drive concluído com sucesso (ID: {drive_file['id']}).")
            return True

        except Exception as e:
            logger.error(f"Erro durante upload do arquivo '{path.name}' para o Google Drive: {e}", exc_info=True)
            return False
