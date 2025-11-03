from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pyairtable import Api
import os

# --- imports for contract generation ---
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

TEMPLATE_FILE = "templates/regContract.txt"

def load_template():
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

# ------------------ FASTAPI SETUP ------------------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_ID = os.getenv("AIRTABLE_TABLE_ID")

api = Api(AIRTABLE_API_KEY)

@app.get("/")
def home():
    return {"status": "ok", "message": "Backend running"}

@app.post("/update")
async def update_airtable(request: Request):
    try:
        data = await request.json()
        record_data = data.get("record")

        if not record_data:
            return {"error": "No record data provided"}

        table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_ID)
        created_record = table.create(record_data)

        return {"status": "success", "record": created_record}

    except Exception as e:
        print("❌ Error updating Airtable:", e)
        return {"status": "error", "message": str(e)}

# ------------------ NEW CONTRACT ROUTE ------------------

@app.post("/generate-contract")
async def create_contract(request: Request):
    try:
        data = await request.json()
        record = data.get("record")

        if not record:
            return {"error": "No record provided"}

        required_fields = [
            "contractor_name", "signer_name", "relationship_to_vendor",
            "address", "email", "vendor_account",
            "service", "amount", "due_date", "end_date"
        ]

        missing = [f for f in required_fields if f not in record]
        if missing:
            return {"error": f"Missing required fields: {', '.join(missing)}"}

        pdf_path = generate_contract(record)

        return {"status": "success", "file_path": pdf_path}

    except Exception as e:
        print("❌ Error generating contract:", e)
        return {"status": "error", "message": str(e)}
