# RPA E-mail Processing, Document Data Extraction & Google Drive Automation

Sistema de Automação de Processos Robóticos (RPA) para leitura de e-mails não lidos (IMAP/SMTP), extração inteligente de dados estruturados (Nome, CPF, Data de Nascimento, Endereço) a partir de documentos (PDF, DOCX, TXT), consolidação em Planilha Mestra Excel e sincronização automática com o Google Drive (PyDrive2).

---

## 📌 Estrutura do Projeto (Gitflow)

O projeto foi construído utilizando a metodologia **Gitflow**, composto por 3 *features*:

1. **`feature/ler-emails`**: Leitura de e-mails não lidos via IMAP SSL, extração de anexos, classificação em pastas (`Documentos_OK`, `Pendentes`, `Arquivados`) e confirmação automática por e-mail via SMTP.
2. **`feature/acessar-documento`**: Leitura de arquivos PDF (`pypdf`), DOCX (`python-docx`) e TXT, extração via Regex/regras inteligentes de Nome, CPF, Data de Nascimento e Endereço, e geração/atualização da `planilha_mestra.xlsx` (`openpyxl`).
3. **`feature/salvar-driver` (Atual)**: Integração com o Google Drive via PyDrive2 para upload automático da Planilha Mestra Excel e dos documentos processados.

---

## 🛠️ Funcionalidades Principais

- **Módulo 1 (`source/ler_emails`)**:
  - Conexão IMAP SSL segura com busca por mensagens não lidas (`UNSEEN`).
  - Salvamento automatizado de anexos com sanitização de nomes e controle de duplicatas.
  - Notificação de confirmação enviada ao remetente via SMTP.

- **Módulo 2 (`source/acessar_documento`)**:
  - Leitura multi-formato de texto em documentos da pasta `Documentos_OK/`.
  - Extração inteligente de campos:
    - **Nome**: Reconhecimento por rótulos (ex: `Nome do Cliente:`) ou fallback em títulos/cabeçalhos.
    - **CPF**: Validação e formatação para `xxx.xxx.xxx-xx`.
    - **Data de Nascimento**: Detecção de formatos `dd/mm/yyyy` e variações.
    - **Endereço**: Reconhecimento de vias (`Rua`, `Avenida`, `Alameda`) e logradouros.
  - Gravação acumulativa e formatada na Planilha Mestra Excel (`output/planilha_mestra.xlsx`).

- **Módulo 3 (`source/salvar_drive`)**:
  - Conexão e autenticação no Google Drive usando `PyDrive2`.
  - Criação automática de pastas remotas (`RPA_Processos_Automacao/Documentos_Lidos` e `Planilhas_Mestras`).
  - Upload/Atualização remota da Planilha Mestra e dos documentos lidos.
  - Execução graciosa offline (se o arquivo `client_secrets.json` não estiver presente, alerta o usuário e prossegue a execução local).

---

## 🚀 Como Executar

### 1. Requisitos
- Python 3.10 ou superior.

### 2. Configurar Variáveis de Ambiente (.env)
Copie o arquivo `.env.example` para `.env`:
```bash
cp .env.example .env
```

Preencha com as credenciais do seu e-mail e Google Drive:
```env
# IMAP (Leitura)
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
IMAP_USER=seu_email@gmail.com
IMAP_PASSWORD=sua_senha_de_app

# SMTP (Envio)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_de_app
SMTP_USE_TLS=true

# Google Drive (Opcional para upload remoto)
GOOGLE_DRIVE_FOLDER_ID=
GOOGLE_DRIVE_CLIENT_SECRETS_PATH=client_secrets.json
GOOGLE_DRIVE_SETTINGS_PATH=settings.yaml
```

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 4. Gerar PDFs de Exemplo (Opcional para testes)
```bash
python scripts/create_sample_pdf.py
```

### 5. Executar o RPA Completo
```bash
python main.py
```

### 6. Executar os Testes Unitários e Cobertura (Pytest)
```bash
python -m pytest --cov=source --cov-report=term-missing
```

---

## 📂 Arquitetura do Projeto

```
├── main.py                                  # Ponto de entrada do RPA (Etapas 1, 2 e 3)
├── source/
│   ├── ler_emails/                          # Módulo 1: Conexão IMAP/SMTP e gestão de anexos
│   ├── acessar_documento/                   # Módulo 2: Leitura, Regex e Planilha Mestra Excel
│   └── salvar_drive/                        # Módulo 3: Wrapper PyDrive2 e upload Google Drive
├── tests/                                   # Suíte de testes unitários (43 testes passing)
│   ├── test_ler_emails.py
│   ├── test_acessar_documento.py
│   └── test_salvar_drive.py
├── scripts/
│   └── create_sample_pdf.py                  # Script auxiliar para geração de PDFs de teste
├── output/
│   └── planilha_mestra.xlsx                 # Planilha Excel acumulativa gerada pelo RPA
├── .env.example                             # Template com variáveis de ambiente
└── .gitignore                               # Ignora credenciais, caches, PDFs e planilhas geradas
```