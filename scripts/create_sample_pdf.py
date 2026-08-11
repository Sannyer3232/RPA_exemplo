import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

def create_sample_pdf(output_path: Path, title: str, name: str, cpf: str, dob: str, address: str):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=letter)
    width, height = letter

    # Cabeçalho
    c.setFillColor(colors.HexColor("#1F4E78"))
    c.rect(0, height - 80, width, 80, fill=True, stroke=False)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 50, title)

    # Subtítulo
    c.setFillColor(colors.HexColor("#333333"))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, height - 120, "Ficha de Cadastro de Cliente / Titular")

    # Linha divisória
    c.setStrokeColor(colors.HexColor("#CCCCCC"))
    c.setLineWidth(1)
    c.line(40, height - 130, width - 40, height - 130)

    # Conteúdo dos campos
    y = height - 160
    c.setFont("Helvetica-Bold", 12)

    fields = [
        ("Nome do Cliente:", name),
        ("CPF:", cpf),
        ("Data de Nascimento:", dob),
        ("Endereço:", address)
    ]

    for label, val in fields:
        c.setFillColor(colors.HexColor("#1F4E78"))
        c.drawString(40, y, label)
        c.setFillColor(colors.HexColor("#111111"))
        c.setFont("Helvetica", 12)
        c.drawString(200, y, val)
        c.setFont("Helvetica-Bold", 12)
        y -= 35

    # Rodapé
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor(colors.HexColor("#888888"))
    c.drawString(40, 40, "Documento gerado automaticamente para testes do RPA HyperAutomation.")

    c.save()
    print(f"[SUCESSO] PDF de exemplo criado em: {output_path}")

if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    docs_ok_dir = base_dir / "Documentos_OK"

    create_sample_pdf(
        output_path=docs_ok_dir / "exemplo_cadastro_joao.pdf",
        title="SISTEMA HYPERAUTOMATION - FICHA 001",
        name="João Carlos da Silva",
        cpf="123.456.789-00",
        dob="15/05/1990",
        address="Avenida Paulista, 1500 - Bela Vista - São Paulo / SP"
    )

    create_sample_pdf(
        output_path=docs_ok_dir / "exemplo_cadastro_maria.pdf",
        title="SISTEMA HYPERAUTOMATION - FICHA 002",
        name="Maria Eduarda Santos",
        cpf="987.654.321-99",
        dob="20/10/1985",
        address="Rua das Flores, 250 - Centro - Rio de Janeiro / RJ"
    )
