import os
import re
import logging
from pathlib import Path
from typing import Optional
from source.config import Config

logger = logging.getLogger(__name__)

class FileManager:
    """Gerenciador de arquivos e pastas para salvar os anexos nas pastas Documentos_OK, Pendentes e Arquivados."""

    def __init__(self):
        self.dir_ok = Config.DIR_DOCUMENTOS_OK
        self.dir_pendentes = Config.DIR_PENDENTES
        self.dir_arquivados = Config.DIR_ARQUIVADOS
        self.setup_directories()

    def setup_directories(self) -> None:
        """Cria as pastas necessárias se elas não existirem."""
        for path in [self.dir_ok, self.dir_pendentes, self.dir_arquivados]:
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Diretório verificado/criado: {path.resolve()}")

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Remove caracteres inválidos do nome do arquivo para evitar erros no sistema de arquivos."""
        if not filename:
            return "anexo_sem_nome"
        # Substitui caracteres especiais por underline
        clean_name = re.sub(r'[\\/*?:"<>|]', '_', filename)
        # Remove quebras de linha e espaços nas pontas
        clean_name = clean_name.strip().replace('\r', '').replace('\n', '')
        return clean_name or "anexo_sem_nome"

    def get_target_directory(self, category: str) -> Path:
        """Retorna o caminho do diretório final com base na categoria informada (OK, PENDENTE, ARQUIVADO)."""
        cat_upper = category.upper()
        if cat_upper in ("OK", "DOCUMENTOS_OK", "SUCESSO"):
            return self.dir_ok
        elif cat_upper in ("PENDENTE", "PENDENTES", "REVISAR"):
            return self.dir_pendentes
        elif cat_upper in ("ARQUIVADO", "ARQUIVADOS", "PROCESSADO"):
            return self.dir_arquivados
        else:
            logger.warning(f"Categoria desconhecida '{category}'. Salvando em Pendentes por padrão.")
            return self.dir_pendentes

    def save_attachment(self, file_content: bytes, filename: str, category: str = "OK") -> Optional[Path]:
        """
        Salva o anexo no diretório correspondente.
        
        :param file_content: Conteúdo em bytes do anexo.
        :param filename: Nome original do arquivo.
        :param category: Categoria ("OK", "PENDENTE", "ARQUIVADO").
        :return: Path do arquivo salvo ou None em caso de falha.
        """
        try:
            target_dir = self.get_target_directory(category)
            clean_filename = self.sanitize_filename(filename)
            file_path = target_dir / clean_filename

            # Evita sobrescrever arquivos com o mesmo nome criando sufixo sequencial
            counter = 1
            stem = file_path.stem
            suffix = file_path.suffix
            while file_path.exists():
                file_path = target_dir / f"{stem}_{counter}{suffix}"
                counter += 1

            with open(file_path, "wb") as f:
                f.write(file_content)

            logger.info(f"Anexo salvo com sucesso: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Erro ao salvar anexo '{filename}': {e}", exc_info=True)
            return None
