import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
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
AIRTABLE_BASE_1  = os.getenv("AIRTABLE_BASE_1")  # appigIP8l8Iqr054x
AIRTABLE_TABLE_1 = os.getenv("AIRTABLE_TABLE_1") # tbluk07EG1FpjE6bR

# table 2 = Dummy Community Leaders Data
AIRTABLE_BASE_2  = os.getenv("AIRTABLE_BASE_2")  # app7924YTWUI9YhMK
AIRTABLE_TABLE_2 = os.getenv("AIRTABLE_TABLE_2") # tbl5Tl74DBlHg2805

# table 3 = Purchase Orders (Balance reduce)
AIRTABLE_TABLE_3 = os.getenv("AIRTABLE_TABLE_3")  # tblraarK4k6ygw8hk

api = Api(AIRTABLE_API_KEY)


@app.get("/")
def home():
    return {"status": "ok", "message": "Backend running"}


# ============= CREATE CONTRACT =============
@app.post("/generate-contract")
async def create_contract(request: Request):
    try:
        data = await request.json()
        record = data.get("record")

        if not record:
            return {"error": "No record data provided"}

        # Generate contract PDF
        pdf_path = generate_contract(record)
        contractor = record.get("contractor_name", "Unknown contractor")
        print(f"✅ Contract generated for {contractor}: {pdf_path}")

        return {"status": "success", "file_path": pdf_path}

    except Exception as e:
        print("❌ Error generating contract:", e)
        return {"status": "error", "message": str(e)}


@app.get("/download-contract")
async def download_contract(filename: str):
    file_path = os.path.join(GENERATED_CONTRACTS_DIR, filename)

    if not os.path.exists(file_path):
        print(f"⚠️ Contract download failed (not found): {filename}")
        raise HTTPException(status_code=404, detail="Contract not found")

    print(f"📄 Serving contract download: {file_path}")
    return FileResponse(file_path, media_type="application/pdf", filename=filename)
    
# ============= INVOICE FLOW (3 table logic now) =============
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
        print("➡️ inserting into Airtable1 (freelancer table)...")
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
            if new_balance < 0: new_balance = 0

            print(f"✏️ updating Airtable3 Balance: {current_balance} -> {new_balance}")

            t3.update(po_id, {
                "Balance": new_balance
            })
            print("✅ Airtable3 Balance updated")

        print("🎉 /invoice COMPLETED")

        return {
            "ok": True,
            "airtable1_created": r1,
            "airtable2_updated_records": len(matches),
            "airtable3_balance_updated": len(po_matches)
        }

    except Exception as e:
        print("❌ Error in /invoice:", e)
        return {"status": "error", "message": str(e)}
