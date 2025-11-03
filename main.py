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
        matches = t2.all(formula=f"{{Email (from…)}} = '{email}'")
        print("🔍 matches:", matches)

        if matches:
            rid = matches[0]["id"]
            print("✏️ updating Airtable2 record:", rid)
            t2.update(rid, {
                "Status": "Payment requested",
                "Invoice": [{"url": invoicePdfUrl}]
            })
            print("✅ Airtable2 update done")

        print("🎉 /invoice COMPLETED")

        return {
            "ok": True,
            "airtable1_created": r1,
            "airtable2_updated_records": len(matches)
        }

    except Exception as e:
        print("❌ Error in /invoice:", e)
        return {"status": "error", "message": str(e)}
