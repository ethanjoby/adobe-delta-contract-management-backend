import os
import uuid
import json
import requests

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from pyairtable import Api

from contract import GENERATED_CONTRACTS_DIR, generate_contract

app = FastAPI()

app.mount(
    "/generated_contracts",
    StaticFiles(directory=GENERATED_CONTRACTS_DIR),
    name="generated_contracts",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= ENV VARS =============

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")

# table 1 = Dummy Adobe Freelancer Payments
AIRTABLE_BASE_1  = os.getenv("AIRTABLE_BASE_1")
AIRTABLE_TABLE_1 = os.getenv("AIRTABLE_TABLE_1")

# table 2 = Dummy Community Leaders Data
AIRTABLE_BASE_2  = os.getenv("AIRTABLE_BASE_2")
AIRTABLE_TABLE_2 = os.getenv("AIRTABLE_TABLE_2")

# table 3 = Purchase Orders (Balance reduce)
AIRTABLE_TABLE_3 = os.getenv("AIRTABLE_TABLE_3")


# Community Leaders table for contract generation dropdown
# Using the correct table ID from your Airtable URL
COMMUNITY_LEADERS_BASE = "app7924YTWUI9YhMK"
COMMUNITY_LEADERS_TABLE = "tbl5Tl74DBlHg2805"


# Google Drive OAuth config
DRIVE_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID", "1eKDgZvxW8lecck_CiqdDWVWOmiZjFNry")
OAUTH_TOKEN_JSON = os.getenv("GDRIVE_OAUTH_TOKEN_JSON")  # contents of token.json

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

api = Api(AIRTABLE_API_KEY)


# ============= GOOGLE DRIVE HELPERS (OAuth) =============
def get_drive_client():
    """
    Returns an authenticated Drive client using OAuth user credentials
    stored in the GDRIVE_OAUTH_TOKEN_JSON env var.
    """
    if not OAUTH_TOKEN_JSON:
        print("⚠️ No GDRIVE_OAUTH_TOKEN_JSON set — skipping Drive upload")
        return None

    try:
        info = json.loads(OAUTH_TOKEN_JSON)
        creds = Credentials.from_authorized_user_info(info, scopes=SCOPES)

        # If the token is expired but has a refresh token, it will auto-refresh
        # when used by the Google API client.
        return build("drive", "v3", credentials=creds)
    except Exception as e:
        print(f"❌ Failed to create Drive client from OAuth token: {e}")
        return None


def upload_pdf_to_drive(pdf_path: str, folder_id: str = DRIVE_FOLDER_ID):
    """
    Uploads PDF to Google Drive folder using OAuth credentials.
    """
    drive = get_drive_client()
    if not drive:
        return None

    if not os.path.exists(pdf_path):
        print(f"⚠️ File not found, skipping Drive upload: {pdf_path}")
        return None

    metadata = {
        "name": os.path.basename(pdf_path),
        "parents": [folder_id],
    }
    media = MediaFileUpload(pdf_path, mimetype="application/pdf")

    try:
        file = (
            drive.files()
            .create(body=metadata, media_body=media, fields="id, webViewLink")
            .execute()
        )
        print(f"☁️ Uploaded to Drive: {file}")
        return file
    except Exception as e:
        print(f"❌ Drive upload failed: {e}")
        return None


def download_temp_pdf(url: str):
    """
    Downloads the invoice PDF to /tmp and returns its filepath.
    """
    try:
        resp = requests.get(url)
        resp.raise_for_status()

        tmp_path = f"/tmp/{uuid.uuid4()}.pdf"
        with open(tmp_path, "wb") as f:
            f.write(resp.content)

        print(f"⬇️ Downloaded temporary PDF: {tmp_path}")
        return tmp_path
    except Exception as e:
        print(f"❌ Failed to download invoice PDF: {e}")
        return None


@app.get("/")
def home():
    return {"status": "ok", "message": "Backend running"}

# ============= CONTRACTORS ENDPOINT FOR DROPDOWN =============
@app.get("/contractors")
async def get_contractors():
    """
    Fetch all contractors from Community Leaders table for contract generation dropdown
    """
    try:
        print("📋 Fetching contractors from Airtable...")
        table = api.table(COMMUNITY_LEADERS_BASE, COMMUNITY_LEADERS_TABLE)
        records = table.all()
        
        # Transform records to simplified format
        contractors = []
        for record in records:
            try:
                fields = record.get('fields', {})
                
                # Extract email
                email_field = fields.get('Email (from Community Member)', [])
                
                # Handle different formats
                if isinstance(email_field, list) and len(email_field) > 0:
                    email = email_field[0]
                elif isinstance(email_field, str):
                    email = email_field
                else:
                    email = ""
                
                # Extract rate/amount from Rate Formula field - with extra safety
                rate_formula = fields.get('Rate Formula', '')
                amount = ""
                
                if rate_formula:
                    if isinstance(rate_formula, (int, float)):
                        # If it's already a number, just convert to string
                        amount = str(rate_formula)
                    elif isinstance(rate_formula, str):
                        # If it's a string like "$3,000.00", clean it up
                        amount = rate_formula.replace('$', '').replace(',', '').strip()
                    else:
                        # Unknown type, convert to string
                        amount = str(rate_formula)
                
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
                
            except Exception as record_error:
                # Skip this record but continue processing others
                print(f"⚠️ Error processing record {record.get('id', 'unknown')}: {record_error}")
                continue
        
        print(f"✅ Found {len(contractors)} contractors")
        return {"status": "success", "contractors": contractors}
    
    except Exception as e:
        print("❌ Error fetching contractors:", e)
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


# ============= CREATE CONTRACT =============
@app.post("/generate-contract")
async def create_contract(request: Request):
    try:
        data = await request.json()
        record = data.get("record")

        if not record:
            return {"error": "No record data provided"}

        docx_path = generate_contract(record)
        contractor = record.get("contractor_name", "Unknown contractor")
        print(f"✅ Contract generated for {contractor}: {docx_path}")

        # Upload to Google Drive (optional - if PO folder feature is enabled)
        # drive_file = upload_pdf_to_drive(docx_path)

        if not os.path.exists(docx_path):
            raise HTTPException(status_code=404, detail="Contract file not found")
        
        filename = os.path.basename(docx_path)
        return FileResponse(
            docx_path, 
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=filename
        )

    except Exception as e:
        print("❌ Error generating contract:", e)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download-contract")
async def download_contract(filename: str):
    file_path = os.path.join(GENERATED_CONTRACTS_DIR, filename)

    if not os.path.exists(file_path):
        print(f"⚠️ Contract not found: {filename}")
        raise HTTPException(status_code=404, detail="Contract not found")

    print(f"📄 Serving contract download: {file_path}")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)


# ============= INVOICE FLOW =============
@app.post("/invoice")
async def process_invoice(request: Request):
    try:
        print("📌 /invoice endpoint HIT")

        data = await request.json()
        print("📨 Incoming payload:", data)

        paymentName   = data.get("paymentName")
        invoiceDate   = data.get("invoiceDate")
        description   = data.get("description")
        totalPayment  = data.get("totalPayment")
        purchaseOrder = data.get("purchaseOrder")
        email         = data.get("email")
        invoicePdfUrl = data.get("invoicePdfUrl")

        # ---------- TABLE 1 INSERT ----------
        print("➡️ inserting into Airtable1...")
        t1 = api.table(AIRTABLE_BASE_1, AIRTABLE_TABLE_1)
        r1 = t1.create({
            "Payment Name":    paymentName,
            "Invoice Date":    invoiceDate,
            "Description":     description,
            "Total Payment":   totalPayment,
            "Purchase Orders": purchaseOrder
        })
        print("✅ Airtable1 insert OK:", r1)

        # ---------- TABLE 2 UPDATE ----------
        print(f"🔎 searching Airtable2 for email: {email}")
        t2 = api.table(AIRTABLE_BASE_2, AIRTABLE_TABLE_2)
        matches = t2.all(formula=f"{{Email (from Community Member)}} = '{email}'")
        print("🔍 matches:", matches)

        if matches:
            rid = matches[0]["id"]
            print("✏️ updating Airtable2 record:", rid)
            t2.update(rid, {
                "Status": "Payment requested",
                "Invoice": [{"url": invoicePdfUrl}]
            })
            print("✅ Airtable2 update done")

        # ---------- TABLE 3 BALANCE SUBTRACT ----------
        print(f"🔎 searching Airtable3 for purchaseOrder: {purchaseOrder}")
        t3 = api.table(AIRTABLE_BASE_1, AIRTABLE_TABLE_3)
        po_matches = t3.all(formula=f"{{Orders}} = '{purchaseOrder}'")
        print("🔍 PO matches:", po_matches)

        if po_matches:
            po_id = po_matches[0]["id"]
            po_rec = po_matches[0]["fields"]
            current_balance = po_rec.get("Balance", 0)

            new_balance = current_balance - totalPayment
            if new_balance < 0:
                new_balance = 0

            print(f"✏️ updating Airtable3 Balance: {current_balance} -> {new_balance}")
            t3.update(po_id, {"Balance": new_balance})
            print("✅ Airtable3 Balance updated")

        # ---------- GOOGLE DRIVE UPLOAD OF INVOICE PDF ----------
        drive_upload_file = None

        if invoicePdfUrl:
            print(f"⬇️ Downloading invoice PDF for Drive upload: {invoicePdfUrl}")
            temp_pdf = download_temp_pdf(invoicePdfUrl)

            if temp_pdf:
                print(f"☁️ Uploading invoice PDF to Google Drive: {temp_pdf}")
                drive_upload_file = upload_pdf_to_drive(temp_pdf)

        print("🎉 /invoice COMPLETED")

        return {
            "ok": True,
            "airtable1_created": r1,
            "airtable2_updated_records": len(matches),
            "airtable3_balance_updated": len(po_matches),
            "drive_file": drive_upload_file,
        }

    except Exception as e:
        print("❌ Error in /invoice:", e)
        return {"status": "error", "message": str(e)}
