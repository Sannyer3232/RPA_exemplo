import logging
from pathlib import Path
from typing import Dict, Any, Optional
from source.ler_emails.config import Config
from source.salvar_drive.drive_uploader import GoogleDriveUploader

logger = logging.getLogger(__name__)

class DriveProcessor:
    """Orquestrador do upload da Planilha Mestra e dos documentos lidos para o Google Drive."""

    def __init__(
        self,
        uploader: Optional[GoogleDriveUploader] = None,
        docs_dir: Optional[Path] = None,
        excel_path: Optional[Path] = None
    ):
        self.uploader = uploader or GoogleDriveUploader()
        self.docs_dir = Path(docs_dir) if docs_dir else Config.DIR_DOCUMENTOS_OK
        
        if excel_path:
            self.excel_path = Path(excel_path)
        else:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.excel_path = base_dir / "output" / "planilha_mestra.xlsx"

    def run_upload_pipeline(self) -> Dict[str, Any]:
        """
        Executa o pipeline de upload no Google Drive:
        1. Autenticação no Google Drive
        2. Upload da Planilha Mestra Excel
        3. Upload de todos os documentos lidos na pasta Documentos_OK
        
        :return: Estatísticas do upload.
        """
        stats = {
            "autenticado": False,
            "planilha_enviada": False,
            "documentos_enviados": 0,
            "falhas_upload": 0
        }

        logger.info("Iniciando processo de upload para o Google Drive...")
        
        # 1. Autenticação
        authenticated = self.uploader.authenticate()
        stats["autenticado"] = authenticated

        if not authenticated:
            logger.warning(
                "Upload para o Google Drive ignorado: credenciais não configuradas ou falha na autenticação. "
                "Para ativar, forneça o arquivo 'client_secrets.json'."
            )
            return stats

        # 2. Criação / Obtenção das Pastas Remotas no Drive
        main_folder_id = self.uploader.get_or_create_folder("RPA_Processos_Automacao")
        docs_folder_id = self.uploader.get_or_create_folder("Documentos_Lidos", parent_id=main_folder_id)
        excel_folder_id = self.uploader.get_or_create_folder("Planilhas_Mestras", parent_id=main_folder_id)

        # 3. Upload da Planilha Mestra Excel
        if self.excel_path.exists():
            logger.info(f"Enviando Planilha Mestra '{self.excel_path.name}' para o Google Drive...")
            success_excel = self.uploader.upload_file(
                file_path=self.excel_path,
                folder_id=excel_folder_id
            )
            stats["planilha_enviada"] = success_excel
            if not success_excel:
                stats["falhas_upload"] += 1
        else:
            logger.warning(f"Planilha Mestra não encontrada em '{self.excel_path}'. Upload da planilha ignorado.")

        # 4. Upload dos Documentos Lidos (Documentos_OK)
        if self.docs_dir.exists():
            files_to_upload = [f for f in self.docs_dir.iterdir() if f.is_file() and not f.name.startswith('.')]
            logger.info(f"Enviando {len(files_to_upload)} documento(s) de '{self.docs_dir.name}' para o Google Drive...")

            for file_path in files_to_upload:
                success_doc = self.uploader.upload_file(
                    file_path=file_path,
                    folder_id=docs_folder_id
                )
                if success_doc:
                    stats["documentos_enviados"] += 1
                else:
                    stats["falhas_upload"] += 1
        else:
            logger.warning(f"Diretório de documentos '{self.docs_dir}' não encontrado.")

        logger.info(f"Processo de upload para o Google Drive finalizado. Estatísticas: {stats}")
        return stats
