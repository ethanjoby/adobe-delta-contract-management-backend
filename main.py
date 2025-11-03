from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
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

# ============= ENV VARS =============

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")

# table 1 = Dummy Adobe Freelancer Payments
AIRTABLE_BASE_1  = os.getenv("AIRTABLE_BASE_1")  # appigIP8l8Iqr054x
AIRTABLE_TABLE_1 = os.getenv("AIRTABLE_TABLE_1") # tbluk07EG1FpjE6bR

# table 2 = Dummy Community Leaders Data
AIRTABLE_BASE_2  = os.getenv("AIRTABLE_BASE_2")  # app7924YTWUI9YhMK
AIRTABLE_TABLE_2 = os.getenv("AIRTABLE_TABLE_2") # tbl5Tl74DBlHg2805

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

        pdf_path = generate_contract(record)
        return {"status": "success", "file_path": pdf_path}

    except Exception as e:
        print("❌ Error generating contract:", e)
        return {"status": "error", "message": str(e)}


# ============= INVOICE FLOW (2 table logic) =============

@app.post("/invoice")
async def process_invoice(request: Request):
    try:
        data = await request.json()

        paymentName   = data.get("paymentName")
        invoiceDate   = data.get("invoiceDate")
        description   = data.get("description")
        totalPayment  = data.get("totalPayment")
        purchaseOrder = data.get("purchaseOrder")
        email         = data.get("email")
        invoicePdfUrl = data.get("invoicePdfUrl")  # already uploaded by FE

        # ---------- TABLE 1 INSERT ----------
        t1 = api.table(AIRTABLE_BASE_1, AIRTABLE_TABLE_1)
        r1 = t1.create({
            "Payment Name":    paymentName,
            "Invoice Date":    invoiceDate,
            "Description":     description,
            "Total Payment":   totalPayment,
            "Purchase Orders": purchaseOrder
        })

        # ---------- TABLE 2 UPDATE ----------
        t2 = api.table(AIRTABLE_BASE_2, AIRTABLE_TABLE_2)
        matches = t2.all(formula=f"{{Email (from…)}} = '{email}'")

        if matches:
            rid = matches[0]["id"]
            t2.update(rid, {
                "Status": "Payment requested",
                "Invoice": [{"url": invoicePdfUrl}]
            })

        return {
            "ok": True,
            "airtable1_created": r1,
            "airtable2_updated_records": len(matches)
        }

    except Exception as e:
        print("❌ Error in /invoice:", e)
        return {"status": "error", "message": str(e)}
