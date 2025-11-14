import os
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

TEMPLATE_FILE = "templates/regContract.txt"   # always use the regular contract for now
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GENERATED_CONTRACTS_DIR = os.path.join(BASE_DIR, "generated_contracts")

os.makedirs(GENERATED_CONTRACTS_DIR, exist_ok=True)

def load_template() -> str:
    with open(TEMPLATE_FILE, "r") as f:
        return f.read()

def fill_template(template: str, fields: dict) -> str:
    return template.format(**fields)

def generate_pdf(text: str, output_path: str):
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(output_path)
    content = []

    for line in text.split("\n"):
        if line.strip():
            content.append(Paragraph(line, styles["Normal"]))
        content.append(Spacer(1, 5))

    doc.build(content)

def generate_contract(fields: dict) -> str:
    """
    Generates contract PDF using regContract template
    Required fields in dict:
    contractor_name, signer_name, relationship_to_vendor,
    address, email, vendor_account, service, amount, due_date, end_date
    """

    template = load_template()
    filled_text = fill_template(template, fields)

    safe_name = fields["contractor_name"].replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"contract_{safe_name}_{timestamp}.pdf"
    output_path = os.path.join(GENERATED_CONTRACTS_DIR, filename)

    generate_pdf(filled_text, output_path)

    return output_path


# Example local test
if __name__ == "__main__":
    data = {
        "contractor_name": "Kody Alexander Lambourne",
        "signer_name": "",
        "relationship_to_vendor": "",
        "address": "3406 Duval St Unit B Austin TX 78705",
        "email": "contact.bykody@gmail.com",
        "vendor_account": "Needed",
        "service": "Video Promotion",
        "amount": "15000",
        "due_date": "October 30, 2025",
        "end_date": "October 30, 2025"
    }

    path = generate_contract(data)
    print(f"✅ Contract generated at: {path}")
