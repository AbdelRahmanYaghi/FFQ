from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import pandas as pd
import os
import io
from typing import Optional
import json
from pydantic import BaseModel
import traceback
from processes_before_download import process_df_before_download, rows_to_workbook
import xlsxwriter
import math

app = FastAPI(title="FFQ API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = "./data"
os.makedirs(DATA_DIR, exist_ok=True)

FOOD_DATA = json.load(open('portions.json', encoding='utf-8'))
FREQUENCY_OPTIONS = ["", "Per day", "Per week", "Per Month", "Never"]

def build_base_rows():
    rows = []
    for food_code, food_details in FOOD_DATA.items():
        rows.append({
            "id": food_code,
            "name": food_details['name'],
            "portion_size_options": list(food_details['portions'].keys()) + [""],
            "section": food_code.split('.')[0],
            "selected_portion_size": "",
            "number_of_portions": 0,
            "frequency": "",
            "frequency_count": 0,
        })
    return rows

def csv_path(uid: str) -> str:
    return os.path.join(DATA_DIR, f"{uid}_FFQ.csv")

def load_or_create(uid: str) -> list[dict]:
    path = csv_path(uid)
    base = build_base_rows()
    if not os.path.exists(path):
        return base
    try:
        df = pd.read_csv(path, encoding='utf-8').fillna("")
        saved = {r["id"]: r for r in df.to_dict("records")}
        for row in base:
            if row["id"] in saved:
                s = saved[row["id"]]
                if isinstance(s.get("Portion Size Options"), str):
                    row["portion_size_options"] = json.loads(s.get("Portion Size Options")) 
                elif isinstance(s.get("Portion Size Options"), list):
                    row["portion_size_options"] = s.get("Portion Size Options")
                else:
                    row["portion_size_options"] = []
                row["selected_portion_size"] = str(s.get("Selected Portion Size", "") or "")
                row["number_of_portions"]     = float(s.get("Number of Portions", 0) or 0)
                row["frequency"]        = str(s.get("Frequency", ""))
                row["frequency_count"]  = float(s.get("Frequency Count", 0) or 0)
        return base
    except Exception as e:
        print('\n'.join(traceback.format_exception(e)))
        return base

def rows_to_df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame([{
        "id": r["id"],
        "Name": r["name"],
        "Portion Size Options": json.dumps(r["portion_size_options"], ensure_ascii=False),
        "Section": r["section"],
        "Selected Portion Size": r["selected_portion_size"],
        "Number of Portions": r["number_of_portions"],
        "Frequency": r["frequency"],
        "Frequency Count": r["frequency_count"],
    } for r in rows])

def special_rows_to_df(rows: list[dict]) -> pd.DataFrame:    
    return pd.DataFrame(rows)

# ── Models ────────────────────────────────────────────────────────────────────
class FoodRow(BaseModel):
    id: str
    name: str
    portion_size_options: list[str]
    section: str
    selected_portion_size: str = ""
    number_of_portions: float = 0
    frequency: str = ""
    frequency_count: float = 0

class SavePayload(BaseModel):
    rows: list[FoodRow]

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/participants")
def list_participants():
    files = [f.replace("_FFQ.csv", "") for f in os.listdir(DATA_DIR) if f.endswith("_FFQ.csv")]
    return sorted(files)

@app.get("/participants/{uid}")
def get_participant(uid: str):
    return {"uid": uid, "rows": load_or_create(uid)}

@app.post("/participants/{uid}/save")
def save_participant(uid: str, payload: SavePayload):
    rows = [r.model_dump() for r in payload.rows]
    df = rows_to_df(rows)
    df.to_csv(csv_path(uid), index=False, encoding='utf-8')
    return {"ok": True}

@app.delete("/participants/{uid}")
def delete_participant(uid: str):
    path = csv_path(uid)
    if os.path.exists(path):
        os.remove(path)
    return {"ok": True}

@app.get("/participants/{uid}/download")
def download_participant(uid: str):
    rows = load_or_create(uid)
    process_df_before_download(rows)
    workbook, buf = rows_to_workbook(rows)

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{uid}_FFQ.xlsx"'}
    )

@app.get("/meta")
def get_meta():
    return [
     {
        "code": food_code,
        "food name": food_details['name'],
        "frequency_options": FREQUENCY_OPTIONS,
        "Portion Size Options": food_details['portions'],
        "section": food_code.split('.')[0]
    } for food_code, food_details in FOOD_DATA     
    ]

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)