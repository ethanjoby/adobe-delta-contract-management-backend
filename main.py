from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pyairtable import Api
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for production: replace * with your frontend domain
    allow_methods=["*"],
    allow_headers=["*"],
)

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")  # your personal access token
TABLE_NAME = "Performance Overview"               # same as table name in Airtable UI

api = Api(AIRTABLE_API_KEY)

@app.get("/")
def home():
    return {"status": "ok", "message": "Adobe Performance API live"}

@app.post("/update")
async def update_airtable(request: Request):
    data = await request.json()
    record_data = data.get("record", {})

    if not record_data:
        return {"error": "No record data provided"}

    table = api.table(TABLE_NAME)
    created = table.create(record_data)
    return {"status": "success", "record": created}
