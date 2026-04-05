# FFQ Manager

Food Frequency Questionnaire — React + FastAPI

## Project Structure

```
ffq/
├── backend/
│   ├── main.py           # FastAPI app — all routes, data logic, CSV storage
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx       # Main React app
│   │   ├── App.css       # All styles
│   │   ├── api.js        # Fetch helpers (all API calls)
│   │   ├── main.jsx      # Entry point
│   │   └── index.css     # Global CSS / variables
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
└── start.sh              # Dev launcher (runs both servers)
```

## Quick Start

```bash
chmod +x start.sh
./start.sh
```

Then open **http://localhost:5173**

Or run manually:

```bash
# Terminal 1 — Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/participants` | List all participant IDs |
| GET | `/participants/{uid}` | Load participant rows |
| POST | `/participants/{uid}/save` | Save rows to CSV |
| DELETE | `/participants/{uid}` | Delete participant CSV |
| GET | `/participants/{uid}/download` | Download processed CSV |
| GET | `/meta` | Food items, portion options, frequency options |

## Key Features

- **Auto-save every 2 minutes** — only saves if there are unsaved changes (dirty flag)
- **Manual Save button** — instant save at any time
- **Section navigation** — click any food group in the left panel to filter the table; click again to show all
- **Progress bar** — tracks what % of items have a frequency selected
- **Download CSV** — passes through `process_csv` hook on the backend before download (extend `main.py` to add calculations)
- **CSV storage** — one file per participant in `backend/data/`

## Adding CSV Processing Logic

In `backend/main.py`, find the `download_participant` route and extend the `# process_csv hook` section:

```python
@app.get("/participants/{uid}/download")
def download_participant(uid: str):
    rows = load_or_create(uid)
    df = rows_to_df(rows)

    # ── Add your calculations here ──────────────────────
    # Example: compute daily frequency
    # df["Daily Frequency"] = df.apply(compute_daily_freq, axis=1)
    # ────────────────────────────────────────────────────

    buf = io.StringIO()
    df.to_csv(buf, index=False)
    ...
```
