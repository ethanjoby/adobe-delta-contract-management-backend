from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

app = FastAPI()

TEMPLATE_FILE = "templates/regContract.txt"   # always use regular template

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
    template = load_template()
    filled_text = fill_template(template, fields)

    safe_name = fields["contractor_name"].replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"contract_{safe_name}_{timestamp}.pdf"
    output_dir = "generated_contracts"

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    generate_pdf(filled_text, output_path)

    return output_path


@app.post("/generate-contract")
async def create_contract(request: Request):

    try:
        data = await request.json()
        record = data.get("record")

        if not record:
            return JSONResponse({"error": "No record data provided"}, status_code=400)

        required_fields = [
            "contractor_name", "signer_name", "relationship_to_vendor",
            "address", "email", "vendor_account",
            "service", "amount", "due_date", "end_date"
        ]

        missing = [f for f in required_fields if f not in record]
        if missing:
            return JSONResponse(
                {"error": f"Missing required fields: {', '.join(missing)}"},
                status_code=400
            )

        pdf_path = generate_contract(record)

        return {"status": "success", "file_path": pdf_path}

    except Exception as e:
        print("❌ Error generating contract:", e)
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
