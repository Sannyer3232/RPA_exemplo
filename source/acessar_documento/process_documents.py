import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from source.ler_emails.config import Config
from source.acessar_documento.document_reader import DocumentReader
from source.acessar_documento.data_extractor import DataExtractor
from source.acessar_documento.excel_handler import ExcelHandler

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Orquestrador do processamento de documentos: leitura, extração de dados e salvamento em Planilha Mestra."""

    def __init__(self, input_dir: Optional[Path] = None, excel_path: Optional[Path] = None):
        self.input_dir = Path(input_dir) if input_dir else Config.DIR_DOCUMENTOS_OK
        self.excel_handler = ExcelHandler(file_path=excel_path)

    def process_all_documents(self) -> Dict[str, Any]:
        """
        Varre todos os documentos na pasta Documentos_OK, extrai dados e grava na Planilha Mestra.

        :return: Estatísticas do processamento.
        """
        stats = {
            "documentos_encontrados": 0,
            "documentos_processados": 0,
            "registros_completos": 0,
            "registros_parciais": 0,
            "falhas_leitura": 0
        }

        if not self.input_dir.exists():
            logger.warning(f"Diretório de documentos '{self.input_dir}' não existe.")
            return stats

        files = [f for f in self.input_dir.iterdir() if f.is_file() and not f.name.startswith('.')]
        stats["documentos_encontrados"] = len(files)

        if not files:
            logger.info(f"Nenhum documento encontrado para processar na pasta '{self.input_dir}'.")
            return stats

        logger.info(f"Iniciando leitura e extração de {len(files)} documento(s) em '{self.input_dir}'...")

        for file_path in files:
            try:
                text_content = DocumentReader.read_text(file_path)
                if not text_content:
                    logger.warning(f"Arquivo '{file_path.name}' está vazio ou não pôde ser lido.")
                    stats["falhas_leitura"] += 1
                    extracted_data = {
                        "nome": "NÃO ENCONTRADO",
                        "cpf": "NÃO ENCONTRADO",
                        "data_nascimento": "NÃO ENCONTRADO",
                        "endereco": "NÃO ENCONTRADO",
                        "status": "ERRO_LEITURA",
                        "arquivo_origem": file_path.name
                    }
                else:
                    extracted_data = DataExtractor.extract_all(text_content, source_filename=file_path.name)
                
                saved = self.excel_handler.append_record(extracted_data)
                if saved:
                    stats["documentos_processados"] += 1
                    status = extracted_data.get("status")
                    if status == "COMPLETO":
                        stats["registros_completos"] += 1
                    elif status == "PARCIAL":
                        stats["registros_parciais"] += 1

            except Exception as e:
                logger.error(f"Erro ao processar o documento '{file_path.name}': {e}", exc_info=True)
                stats["falhas_leitura"] += 1

        logger.info(f"Processamento de documentos finalizado. Estatísticas: {stats}")
        return stats
