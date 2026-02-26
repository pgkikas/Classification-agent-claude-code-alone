"""
FastAPI backend for the classification UI.

Endpoints:
  POST /api/classify  — upload a PDF, run agent, return result JSON
  POST /api/save      — save (possibly edited) result JSON to output/

Run:
    uvicorn api:app --port 8000 --reload
"""
import os, sys, json, shutil, tempfile

# Make sure lookup.py and agent.py are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(title="Classification Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import agent lazily so startup is fast
_classify = None

def get_classify():
    global _classify
    if _classify is None:
        from agent import classify
        _classify = classify
    return _classify


@app.post("/api/classify")
async def classify_pdf(file: UploadFile = File(...)):
    """Accept a PDF upload, run the classification agent, return structured JSON."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Save upload to a temp file (agent needs a real path for fitz)
    suffix = os.path.splitext(file.filename)[1] or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        classify = get_classify()
        result = classify(tmp_path)
        # Override document_file with the original upload filename
        result["document_file"] = file.filename
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp_path)


@app.post("/api/save")
async def save_result(result: dict):
    """Save the (possibly edited) result to output/<document_file>.json."""
    doc_file = result.get("document_file", "result.pdf")
    name = os.path.splitext(doc_file)[0]

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(out_dir, exist_ok=True)

    path = os.path.join(out_dir, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return {"saved": True, "path": path}


@app.get("/api/search")
async def search(q: str = ""):
    """
    Combined autocomplete search across accounts (637) and suppliers (6293).
    Returns list of {code, desc, kind} where kind is 'account' or 'supplier'.
    """
    q = q.strip()
    if len(q) < 2:
        return []

    import lookup as lk
    results = []
    seen: set[str] = set()

    # 1. Account code prefix match (e.g. user types "62.07")
    accs = lk.accounts()
    for code, data in accs.items():
        if code.startswith(q) and code not in seen and code.count('.') == 2:
            results.append({"code": code, "desc": data.get("desc", ""), "kind": "account"})
            seen.add(code)
        if len(results) >= 8:
            break

    # 2. Account description keyword search
    kw_results = lk.find_accounts_by_description(q)
    for item in kw_results[:10]:
        if item["code"] not in seen and item["code"].count('.') == 2:
            results.append({"code": item["code"], "desc": item.get("desc", ""), "kind": "account"})
            seen.add(item["code"])

    # 3. Supplier name search (returns 50.xx codes)
    sup_results = lk.search_suppliers_by_name(q, max_results=6)
    for item in sup_results:
        if item["code"] not in seen:
            results.append({"code": item["code"], "desc": item.get("name", ""), "kind": "supplier"})
            seen.add(item["code"])

    return results[:12]


@app.get("/api/health")
async def health():
    return {"status": "ok"}
