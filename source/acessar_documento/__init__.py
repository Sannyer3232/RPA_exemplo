"""
Módulo acessar_documento: Extração de dados (Nome, CPF, Data de Nascimento, Endereço)
a partir de documentos (PDF, DOCX, TXT) e salvamento em Planilha Mestra Excel.
"""
from source.acessar_documento.document_reader import DocumentReader
from source.acessar_documento.data_extractor import DataExtractor
from source.acessar_documento.excel_handler import ExcelHandler
from source.acessar_documento.process_documents import DocumentProcessor

__all__ = ["DocumentReader", "DataExtractor", "ExcelHandler", "DocumentProcessor"]
