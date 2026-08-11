import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env no diretório raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / '.env'

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

class Config:
    """Configurações centralizadas da aplicação RPA obtidas via variáveis de ambiente (.env)."""

    # Configurações do Servidor IMAP
    IMAP_SERVER: str = os.getenv("IMAP_SERVER", "imap.gmail.com")
    IMAP_PORT: int = int(os.getenv("IMAP_PORT", "993"))
    IMAP_USER: str = os.getenv("IMAP_USER", "")
    IMAP_PASSWORD: str = os.getenv("IMAP_PASSWORD", "")

    # Configurações do Servidor SMTP
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() in ("true", "1", "t", "yes")

    # Pastas para salvamento dos anexos
    DIR_DOCUMENTOS_OK: Path = BASE_DIR / os.getenv("DIR_DOCUMENTOS_OK", "Documentos_OK")
    DIR_PENDENTES: Path = BASE_DIR / os.getenv("DIR_PENDENTES", "Pendentes")
    DIR_ARQUIVADOS: Path = BASE_DIR / os.getenv("DIR_ARQUIVADOS", "Arquivados")

    @classmethod
    def validate_imap_config(cls) -> bool:
        """Verifica se as credenciais mínimas do IMAP foram preenchidas."""
        if not cls.IMAP_USER or not cls.IMAP_PASSWORD:
            return False
        return True

    @classmethod
    def validate_smtp_config(cls) -> bool:
        """Verifica se as credenciais mínimas do SMTP foram preenchidas."""
        if not cls.SMTP_USER or not cls.SMTP_PASSWORD:
            return False
        return True
