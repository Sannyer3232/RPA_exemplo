import sys
import logging
from pathlib import Path
from source.ler_emails.config import Config
from source.ler_emails.process_emails import EmailProcessor

def setup_logging():
    """Configura o formato e nível de log da aplicação."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def check_env_file():
    """Verifica se o arquivo .env existe. Se não existir, alerta o usuário."""
    env_file = Path(__file__).resolve().parent / ".env"
    if not env_file.exists():
        print("\n" + "="*70)
        print("[AVISO] Arquivo '.env' não foi encontrado!")
        print("Crie o arquivo '.env' na raiz do projeto com base no '.env.example':")
        print("  cp .env.example .env")
        print("E preencha com as credenciais do seu e-mail (IMAP / SMTP).")
        print("="*70 + "\n")

def main():
    setup_logging()
    logger = logging.getLogger("RPA_Main")
    
    logger.info("=== Iniciando RPA - Feature 1: Leitura de E-mails e Organização de Anexos ===")
    check_env_file()

    if not Config.validate_imap_config():
        logger.warning(
            "Credenciais IMAP ausentes ou não configuradas no arquivo .env. "
            "Por favor, configure IMAP_USER e IMAP_PASSWORD para conectar a caixa de entrada real."
        )

    # Instancia e executa o processador de e-mails
    processor = EmailProcessor(send_confirmation=False)
    
    # mark_as_read=False para testes; marque True em produção
    resultado = processor.process_unread_emails(mark_as_read=False)

    logger.info("=== Summary de Execução do RPA ===")
    logger.info(f" - E-mails não lidos encontrados: {resultado.get('emails_processados', 0)}")
    logger.info(f" - Anexos em Documentos_OK: {resultado.get('anexos_ok', 0)}")
    logger.info(f" - Anexos em Pendentes: {resultado.get('anexos_pendentes', 0)}")
    logger.info(f" - Anexos em Arquivados: {resultado.get('anexos_arquivados', 0)}")
    logger.info(f" - E-mails sem anexo: {resultado.get('emails_sem_anexo', 0)}")
    logger.info("=== Processo Finalizado com Sucesso ===")

if __name__ == "__main__":
    main()
