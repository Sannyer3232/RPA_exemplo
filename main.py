import sys
import logging
from pathlib import Path
from source.ler_emails.config import Config
from source.ler_emails.process_emails import EmailProcessor
from source.acessar_documento.process_documents import DocumentProcessor
from source.salvar_drive.process_upload import DriveProcessor

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
        print("E preencha com as credenciais do seu e-mail (IMAP / SMTP) e Google Drive.")
        print("="*70 + "\n")

def main():
    setup_logging()
    logger = logging.getLogger("RPA_Main")
    
    logger.info("=== Executando RPA HyperAutomation (Completo: E-mails -> Extração -> Google Drive) ===")
    check_env_file()

    # --- ETAPA 1: Leitura de E-mails e Separação de Anexos ---
    logger.info("--- Etapa 1: Leitura de E-mails (IMAP) e Separação de Anexos ---")
    if not Config.validate_imap_config():
        logger.warning(
            "Credenciais IMAP ausentes ou não configuradas no arquivo .env. "
            "Por favor, configure IMAP_USER e IMAP_PASSWORD para conectar à caixa de entrada real."
        )

    email_processor = EmailProcessor(send_confirmation=False)
    res_emails = email_processor.process_unread_emails(mark_as_read=False)

    # --- ETAPA 2: Acesso aos Documentos e Extração para Planilha Mestra ---
    logger.info("--- Etapa 2: Processamento de Documentos e Gravação em Planilha Excel Mestra ---")
    doc_processor = DocumentProcessor()
    res_docs = doc_processor.process_all_documents()

    # --- ETAPA 3: Upload para o Google Drive ---
    logger.info("--- Etapa 3: Upload da Planilha Mestra e Documentos para o Google Drive ---")
    drive_processor = DriveProcessor()
    res_drive = drive_processor.run_upload_pipeline()

    # --- SUMMARY GERAL ---
    logger.info("=== Summary de Execução Geral do RPA ===")
    logger.info("[Etapa 1 - E-mails]")
    logger.info(f" - E-mails processados: {res_emails.get('emails_processados', 0)}")
    logger.info(f" - Anexos em Documentos_OK: {res_emails.get('anexos_ok', 0)}")
    logger.info(f" - Anexos em Pendentes: {res_emails.get('anexos_pendentes', 0)}")
    logger.info(f" - Anexos em Arquivados: {res_emails.get('anexos_arquivados', 0)}")

    logger.info("[Etapa 2 - Extração de Dados & Excel]")
    logger.info(f" - Documentos lidos: {res_docs.get('documentos_encontrados', 0)}")
    logger.info(f" - Registros gravados no Excel: {res_docs.get('documentos_processados', 0)}")
    logger.info(f" - Registros completos (4/4 campos): {res_docs.get('registros_completos', 0)}")
    logger.info(f" - Registros parciais: {res_docs.get('registros_parciais', 0)}")

    logger.info("[Etapa 3 - Google Drive]")
    logger.info(f" - Autenticado no Drive: {res_drive.get('autenticado', False)}")
    logger.info(f" - Planilha Mestra enviada: {res_drive.get('planilha_enviada', False)}")
    logger.info(f" - Documentos enviados: {res_drive.get('documentos_enviados', 0)}")
    logger.info("=== Processo Finalizado com Sucesso ===")

if __name__ == "__main__":
    main()
