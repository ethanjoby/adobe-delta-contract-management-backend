from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pyairtable import Api
import os

from contract import generate_contract

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

# Community Leaders table for contract generation
COMMUNITY_LEADERS_BASE = "app7924YTWUI9YhMK"
COMMUNITY_LEADERS_TABLE = "tbl5Tl74DBlHg2805"

print("🔍 DEBUG ENV:", {
    "AIRTABLE_API_KEY": AIRTABLE_API_KEY[:5] + "..." if AIRTABLE_API_KEY else None,
    "AIRTABLE_BASE_ID": AIRTABLE_BASE_ID,
    "AIRTABLE_TABLE_ID": AIRTABLE_TABLE_ID,
    "COMMUNITY_LEADERS_BASE": COMMUNITY_LEADERS_BASE,
    "COMMUNITY_LEADERS_TABLE": COMMUNITY_LEADERS_TABLE,
})

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

        if not AIRTABLE_BASE_ID or not AIRTABLE_TABLE_ID:
            raise ValueError("Missing Airtable environment variables")

        table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_ID)
        created_record = table.create(record_data)

        return {"status": "success", "record": created_record}

    except Exception as e:
        print("❌ Error updating Airtable:", e)
        return {"status": "error", "message": str(e)}


@app.get("/contractors")
async def get_contractors():
    """
    Fetch all contractors from Community Leaders table for contract generation dropdown
    """
    try:
        table = api.table(COMMUNITY_LEADERS_BASE, COMMUNITY_LEADERS_TABLE)
        records = table.all()
        
        # Transform records to simplified format
        contractors = []
        for record in records:
            fields = record.get('fields', {})
            
            # Extract email - it's in the "Email (from Communit..." field
            email_field = fields.get('Email (from Communit...', [])
            email = email_field[0] if email_field else ""
            
            # Extract rate/amount from Rate Formula field
            rate_formula = fields.get('Rate Formula', '')
            # Convert "$3,000.00" to "3000"
            amount = rate_formula.replace('$', '').replace(',', '').strip() if rate_formula else ""
            
            contractor = {
                'id': record['id'],
                'summary': fields.get('Summary', ''),
                'email': email,
                'date': fields.get('Date', ''),
                'status': fields.get('Status', ''),
                'po': fields.get('PO', ''),
                'amount': amount,
            }
            contractors.append(contractor)
        
        return {"status": "success", "contractors": contractors}
    
    except Exception as e:
        print("❌ Error fetching contractors:", e)
        return {"status": "error", "message": str(e)}


@app.post("/generate-contract")
async def create_contract(request: Request):
    try:
        data = await request.json()
        record = data.get("record")

        if not record:
            return {"error": "No record data provided"}

        # Generate contract PDF
        pdf_path = generate_contract(record)
        
        # Return the PDF file directly
        return FileResponse(
            pdf_path,
            media_type='application/pdf',
            headers={"Content-Disposition": "inline; filename=contract.pdf"}
        )

    except Exception as e:
        print("❌ Error generating contract:", e)
        return {"status": "error", "message": str(e)}
