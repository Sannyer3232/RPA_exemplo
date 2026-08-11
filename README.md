# RPA E-mail Processing & Document Automation

Sistema de Automação de Processos Robóticos (RPA) para leitura automatizada de e-mails não lidos, extração e organização de anexos em pastas estruturadas, envio de respostas automatizadas (SMTP) e posterior integração com planilhas Excel e Google Drive.

## 📌 Estrutura do Projeto (Gitflow)

O projeto foi dividido em 3 *features* principais utilizando o fluxo **Gitflow**:

1. **`feature/ler-emails` (Atual)**: Leitura de e-mails não lidos via IMAP, download de anexos, separação automática nas pastas `Documentos_OK`, `Pendentes` e `Arquivados`, e preparação do envio de respostas via SMTP sem credenciais hardcoded (uso de `.env`).
2. **`feature/acessar-documento`**: Leitura e captura de dados dos anexos/documentos baixados e armazenamento estruturado em planilha Excel.
3. **`feature/salvar-driver`**: Upload automático das planilhas geradas e anexos processados para o Google Drive.

---

## 🛠️ Funcionalidades da Feature 1 (`feature/ler-emails`)

- **Conexão Segura IMAP**: Autenticação e busca por mensagens não lidas (`UNSEEN`).
- **Gestão Segura de Credenciais**: Leitura de variáveis de ambiente do arquivo `.env` via `python-dotenv`.
- **Tratamento de Anexos**: Decodificação MIME de cabeçalhos e nomes de arquivos e sanitização de caracteres inválidos.
- **Organização em Pastas**:
  - `Documentos_OK`: Anexos válidos e processáveis (PDF, DOCX, XLSX, etc.).
  - `Pendentes`: Anexos com extensões não reconhecidas ou e-mails sem anexo.
  - `Arquivados`: Cópia de histórico/backup de todos os anexos e e-mails processados.
- **Módulo SMTP**: Cliente de envio de e-mails configurado para confirmações automáticas de recebimento.
- **Resiliência a Duplicados**: Renomeação automática com sufixos caso existam arquivos com o mesmo nome.

---

## 🚀 Como Executar

### 1. Requisitos
- Python 3.10 ou superior.

### 2. Configurar o Ambiente de Variáveis (.env)
Copie o modelo `.env.example` para `.env`:
```bash
cp .env.example .env
```

Edite o arquivo `.env` com as suas credenciais do servidor de e-mail:
```env
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
IMAP_USER=seu_email@gmail.com
IMAP_PASSWORD=sua_senha_de_app

SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASSWORD=sua_senha_de_app
SMTP_USE_TLS=true
```

> 💡 **Nota para Usuários Gmail / Outlook**: Para contas com verificação em duas etapas, utilize uma **Senha de App** gerada nas configurações de segurança do seu provedor de e-mail.

### 3. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 4. Executar o RPA
```bash
python main.py
```

### 5. Executar os Testes Automatizados
```bash
python -m unittest discover tests
```

---

## 📂 Arquitetura de Módulos

```
├── main.py                    # Ponto de entrada do RPA
├── source/
│   ├── config.py              # Carregamento centralizado de configurações (.env)
│   ├── file_manager.py        # Gestão de pastas (Documentos_OK, Pendentes, Arquivados) e escrita
│   ├── imap_client.py         # Cliente IMAP para busca de mensagens UNSEEN e extração de anexos
│   ├── smtp_client.py         # Cliente SMTP para envio de respostas e notificações
│   └── process_emails.py      # Orquestrador do fluxo da Feature 1
├── tests/
│   └── test_email_rpa.py      # Suíte de testes unitários
├── .env.example               # Template de configuração de variáveis
└── .gitignore                 # Arquivos e pastas ignorados no Git (inclui .env e anexos)
```