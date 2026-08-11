import logging
from pathlib import Path
from typing import List, Dict, Any
from source.config import Config
from source.file_manager import FileManager
from source.imap_client import IMAPClient
from source.smtp_client import SMTPClient

logger = logging.getLogger(__name__)

class EmailProcessor:
    """Orquestrador do RPA de leitura de e-mails, salvamento de anexos e classificacao de documentos."""

    VALID_DOC_EXTENSIONS = {'.pdf', '.docx', '.doc', '.xlsx', '.xls', '.csv', '.png', '.jpg', '.jpeg', '.txt', '.xml'}

    def __init__(self, send_confirmation: bool = False):
        self.file_manager = FileManager()
        self.smtp_client = SMTPClient()
        self.send_confirmation = send_confirmation

    def classify_attachment(self, email_data: Dict[str, Any], attachment_name: str) -> str:
        """
        Determina a pasta de destino para o anexo: 'OK', 'PENDENTE' ou 'ARQUIVADO'.
        
        Regras de Classificacao:
        1. Se o assunto contiver tags explicitas como [OK], [PENDENTE], [ARQUIVAR].
        2. Se a extensao for de um documento valido e suportado -> 'OK'.
        3. Se a extensao nao for reconhecida ou houver pendencia -> 'PENDENTE'.
        """
        subject_upper = email_data.get("subject", "").upper()
        ext = Path(attachment_name).suffix.lower()

        if "[OK]" in subject_upper or "[DOCUMENTO OK]" in subject_upper:
            return "OK"
        elif "[PENDENTE]" in subject_upper or "[REVISAR]" in subject_upper:
            return "PENDENTE"
        elif "[ARQUIVAR]" in subject_upper or "[ARQUIVADO]" in subject_upper:
            return "ARQUIVADO"

        if ext in self.VALID_DOC_EXTENSIONS:
            return "OK"
        else:
            logger.info(f"Extensao '{ext}' do anexo '{attachment_name}' nao reconhecida como documento padrao. Direcionando para Pendentes.")
            return "PENDENTE"

    def process_unread_emails(self, mark_as_read: bool = True) -> Dict[str, int]:
        """
        Executa a leitura dos e-mails nao lidos e salva os anexos nas pastas apropriadas.

        :param mark_as_read: Se True, marca os e-mails processados como lidos no servidor.
        :return: Estatísticas do processamento (e-mails processados, anexos salvos por categoria).
        """
        stats = {
            "emails_processados": 0,
            "anexos_ok": 0,
            "anexos_pendentes": 0,
            "anexos_arquivados": 0,
            "emails_sem_anexo": 0
        }

        if not Config.validate_imap_config():
            logger.error("Credenciais IMAP ausentes ou incompletas no arquivo .env!")
            return stats

        logger.info("Iniciando processo de leitura de e-mails nao lidos via IMAP...")
        
        try:
            with IMAPClient() as imap:
                unread_emails = imap.fetch_unread_emails(mark_as_read=mark_as_read)
                stats["emails_processados"] = len(unread_emails)

                if not unread_emails:
                    logger.info("Nenhum e-mail novo (nao lido) encontrado na caixa de entrada.")
                    return stats

                for email_info in unread_emails:
                    subject = email_info["subject"]
                    sender = email_info["sender"]
                    attachments = email_info["attachments"]

                    logger.info(f"Processando e-mail: Remetente='{sender}' | Assunto='{subject}' | Anexos={len(attachments)}")

                    if not attachments:
                        logger.warning(f"O e-mail '{subject}' nao possui anexos. Registrando como Pendente.")
                        stats["emails_sem_anexo"] += 1
                        
                        # Opcional: Salvar resumo do email sem anexo na pasta Pendentes para posterior analise
                        body_filename = f"email_sem_anexo_{email_info['id']}.txt"
                        email_summary = (
                            f"REMETENTE: {sender}\n"
                            f"ASSUNTO: {subject}\n"
                            f"DATA: {email_info['date']}\n\n"
                            f"CORPO DO E-MAIL:\n{email_info['body_text'] or email_info['body_html']}"
                        )
                        self.file_manager.save_attachment(
                            email_summary.encode('utf-8'),
                            body_filename,
                            category="PENDENTE"
                        )
                    else:
                        for att in attachments:
                            att_name = att["filename"]
                            att_content = att["content"]
                            category = self.classify_attachment(email_info, att_name)

                            saved_path = self.file_manager.save_attachment(
                                att_content,
                                att_name,
                                category=category
                            )

                            if saved_path:
                                if category == "OK":
                                    stats["anexos_ok"] += 1
                                elif category == "PENDENTE":
                                    stats["anexos_pendentes"] += 1
                                elif category == "ARQUIVADO":
                                    stats["anexos_arquivados"] += 1

                                # Também salva uma cópia de backup/histórico na pasta Arquivados
                                if category != "ARQUIVADO":
                                    self.file_manager.save_attachment(
                                        att_content,
                                        f"copia_{att_name}",
                                        category="ARQUIVADO"
                                    )

                    # Envio opcional de e-mail de confirmacao de recebimento via SMTP
                    if self.send_confirmation and sender and "@" in sender:
                        confirm_body = (
                            f"Olá,\n\n"
                            f"Confirmamos o recebimento e processamento automatizado do seu e-mail: '{subject}'.\n"
                            f"Total de anexos identificados: {len(attachments)}.\n\n"
                            f"Atenciosamente,\nEquipe RPA HyperAutomation"
                        )
                        self.smtp_client.send_email(
                            to_address=sender,
                            subject=f"Confirmacao de Recebimento: {subject}",
                            body_text=confirm_body
                        )

        except Exception as e:
            logger.error(f"Erro inesperado durante o processamento dos e-mails: {e}", exc_info=True)

        logger.info(f"Processamento concluído. Estatísticas: {stats}")
        return stats
