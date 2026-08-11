import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DataExtractor:
    """Extrator de dados estruturados (Nome, CPF, Data de Nascimento, Endereço) a partir de texto bruto."""

    # Expressões Regulares
    CPF_PATTERN = re.compile(r'\b(\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11})\b')
    DATE_PATTERN = re.compile(r'\b(0[1-9]|[12][0-9]|3[01])[-/.](0[1-9]|1[012])[-/.](19|20)\d{2}\b')
    
    # Palavras-chave para identificar rotulos
    NAME_KEYWORDS = [r'nome\s*:', r'nome do cliente\s*:', r'titular\s*:', r'paciente\s*:', r'nome\s*-\s*']
    DOB_KEYWORDS = [r'data de nascimento\s*:', r'data nasc\.?\s*:', r'nascimento\s*:', r'dt\.?\s*nasc\.?\s*:']
    ADDRESS_KEYWORDS = [r'endereço\s*:', r'endereco\s*:', r'logradouro\s*:', r'residência\s*:']

    @classmethod
    def extract_cpf(cls, text: str) -> str:
        """Extrai o CPF do texto e formata como xxx.xxx.xxx-xx."""
        matches = cls.CPF_PATTERN.findall(text)
        for match in matches:
            digits = re.sub(r'\D', '', match)
            if len(digits) == 11 and not digits == digits[0] * 11:
                return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
        return "NÃO ENCONTRADO"

    @classmethod
    def extract_dob(cls, text: str) -> str:
        """Extrai a Data de Nascimento do texto."""
        # Tenta primeiro com rótulo explícito
        for kw in cls.DOB_KEYWORDS:
            match = re.search(kw + r'\s*(' + cls.DATE_PATTERN.pattern + r')', text, re.IGNORECASE)
            if match:
                return match.group(1)

        # Se não houver rótulo, busca a primeira data compatível
        matches = cls.DATE_PATTERN.findall(text)
        if matches:
            match = re.search(cls.DATE_PATTERN, text)
            if match:
                return match.group(0)
        
        return "NÃO ENCONTRADO"

    @classmethod
    def extract_name(cls, text: str) -> str:
        """Extrai o Nome da pessoa do texto (suporta rótulo na mesma linha ou na linha seguinte)."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        for i, line in enumerate(lines):
            for kw in cls.NAME_KEYWORDS:
                # Caso A: Rótulo e valor na mesma linha -> "Nome: João Silva"
                match_same_line = re.search(kw + r'\s*([A-Za-zÀ-ÖØ-öø-ÿ\s]{3,60})', line, re.IGNORECASE)
                if match_same_line:
                    val = match_same_line.group(1).strip()
                    if len(val.split()) >= 1 and not any(k in val.lower() for k in ['cpf', 'data', 'endereço', 'rua', 'ficha', 'sistema']):
                        return val.title()

                # Caso B: Linha contém apenas o rótulo (ex: "Nome do Cliente:") e o valor está na próxima linha
                match_label_only = re.search(r'^\s*' + kw + r'\s*$', line, re.IGNORECASE)
                if match_label_only and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    clean_next = re.sub(r'[^A-Za-zÀ-ÖØ-öø-ÿ\s]', '', next_line).strip()
                    if clean_next and not any(k in next_line.lower() for k in ['cpf:', 'data:', 'endereço:', 'rua:', 'ficha', 'sistema', 'hyperautomation']):
                        return next_line.title()

        # Fallback: Procura nas primeiras linhas que pareçam um nome completo (descartando títulos/cabeçalhos)
        HEADER_KEYWORDS = ['sistema', 'hyperautomation', 'ficha', 'documento', 'relatorio', 'cadastro', 'cpf', 'atendimento', 'processo']
        for line in lines[:5]:
            clean_line = re.sub(r'[^A-Za-zÀ-ÖØ-öø-ÿ\s]', '', line).strip()
            words = clean_line.split()
            if 2 <= len(words) <= 5 and not any(k in clean_line.lower() for k in HEADER_KEYWORDS):
                return clean_line.title()

        return "NÃO ENCONTRADO"

    @classmethod
    def extract_address(cls, text: str) -> str:
        """Extrai o Endereço do texto (suporta rótulo na mesma linha ou na linha seguinte)."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        for i, line in enumerate(lines):
            for kw in cls.ADDRESS_KEYWORDS:
                match = re.search(kw + r'\s*(.+)', line, re.IGNORECASE)
                if match:
                    addr = match.group(1).strip()
                    if addr and not any(k in addr.lower() for k in ['cpf:', 'data:']):
                        return addr

                match_label_only = re.search(r'^\s*' + kw + r'\s*$', line, re.IGNORECASE)
                if match_label_only and i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line and not any(k in next_line.lower() for k in ['cpf:', 'data:', 'nome:']):
                        return next_line

        # Fallback por CEP ou nomes de logradouro (Rua, Av, Avenida, Alameda)
        street_pattern = re.compile(r'\b(rua|av\.?|avenida|alameda|praça|travessa)\s+[^\n]+', re.IGNORECASE)
        match_street = street_pattern.search(text)
        if match_street:
            return match_street.group(0).strip()

        return "NÃO ENCONTRADO"


    @classmethod
    def extract_all(cls, text: str, source_filename: str = "") -> Dict[str, str]:
        """
        Extrai todos os campos alvo do texto e retorna um dicionário estruturado.
        
        :param text: Texto lido do documento.
        :param source_filename: Nome do arquivo de origem.
        :return: Dicionário com Nome, CPF, Data de Nascimento, Endereço e Status.
        """
        if not text.strip():
            return {
                "nome": "NÃO ENCONTRADO",
                "cpf": "NÃO ENCONTRADO",
                "data_nascimento": "NÃO ENCONTRADO",
                "endereco": "NÃO ENCONTRADO",
                "status": "ERRO_LEITURA_VAZIA",
                "arquivo_origem": source_filename
            }

        nome = cls.extract_name(text)
        cpf = cls.extract_cpf(text)
        dob = cls.extract_dob(text)
        address = cls.extract_address(text)

        # Status da extração
        found_count = sum(1 for v in [nome, cpf, dob, address] if v != "NÃO ENCONTRADO")
        if found_count == 4:
            status = "COMPLETO"
        elif found_count > 0:
            status = "PARCIAL"
        else:
            status = "FALHA_EXTRACAO"

        return {
            "nome": nome,
            "cpf": cpf,
            "data_nascimento": dob,
            "endereco": address,
            "status": status,
            "arquivo_origem": source_filename
        }
