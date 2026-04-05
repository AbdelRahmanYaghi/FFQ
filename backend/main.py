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
from processes_before_download import process_df_before_download

app = FastAPI(title="FFQ API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = "./data"
os.makedirs(DATA_DIR, exist_ok=True)

FOOD_DATA = json.load(open('portions.json'))
FREQUENCY_OPTIONS = ["", "Per day", "Per week", "Per Month", "Never"]

def build_base_rows():
    rows = []
    for food_code, food_details in FOOD_DATA.items():
        rows.append({
            "id": food_code,
            "name": food_details['name'],
            "portion_options": list(food_details['portions'].keys()) + [""],
            "section": food_code.split('.')[0],
            "selected_portion_option": "",
            "portion_size": 0,
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
        df = pd.read_csv(path).fillna("")
        saved = {r["id"]: r for r in df.to_dict("records")}
        for row in base:
            if row["id"] in saved:
                s = saved[row["id"]]
                if isinstance(s.get("portion_options"), str):
                    row["portion_options"] = json.loads(s.get("portion_options")) 
                elif isinstance(s.get("portion_options"), list):
                    row["portion_options"] = s.get("portion_options")
                else:
                    row["portion_options"] = []
                row["selected_portion_option"] = str(s.get("selected_portion_option", "") or "")
                row["portion_size"]     = float(s.get("Portion Size", 0) or 0)
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
        "portion_options": json.dumps(r["portion_options"]),
        "Section": r["section"],
        "selected_portion_option": r["selected_portion_option"],
        "Portion Size": r["portion_size"],
        "Frequency": r["frequency"],
        "Frequency Count": r["frequency_count"],
    } for r in rows])

def special_rows_to_df(rows: list[dict]) -> pd.DataFrame:    
    return pd.DataFrame(rows)

# ── Models ────────────────────────────────────────────────────────────────────
class FoodRow(BaseModel):
    id: str
    name: str
    portion_options: list[str]
    section: str
    selected_portion_option: str = ""
    portion_size: float = 0
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
    df.to_csv(csv_path(uid), index=False)
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
    df = special_rows_to_df(rows)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{uid}_FFQ.csv"'}
    )

@app.get("/meta")
def get_meta():
    return [
     {
        "code": food_code,
        "food name": food_details['name'],
        "frequency_options": FREQUENCY_OPTIONS,
        "portion options": food_details['portions'],
        "section": food_code.split('.')[0]
    } for food_code, food_details in FOOD_DATA     
    ]
