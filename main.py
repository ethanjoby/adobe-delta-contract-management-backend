from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pyairtable import Api
import os

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

print("🔍 DEBUG ENV:", {
    "AIRTABLE_API_KEY": AIRTABLE_API_KEY[:5] + "...",
    "AIRTABLE_BASE_ID": AIRTABLE_BASE_ID,
    "AIRTABLE_TABLE_ID": AIRTABLE_TABLE_ID,
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

        # Make sure both IDs exist
        if not AIRTABLE_BASE_ID or not AIRTABLE_TABLE_ID:
            raise ValueError("Missing Airtable environment variables")

        table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_ID)
        created_record = table.create(record_data)

        return {"status": "success", "record": created_record}

    except Exception as e:
        print("❌ Error updating Airtable:", e)
        return {"status": "error", "message": str(e)}
