"""
FastAPI backend for the classification UI.

Endpoints:
  POST /api/classify           — upload a PDF, run agent, return result JSON
  POST /api/save               — save (possibly edited) result JSON to output/
  POST /api/chat               — conversational review of a classification
  GET  /api/history            — list saved classifications (summaries)
  GET  /api/history/{filename} — load a single saved classification
  DELETE /api/history/{filename} — delete a saved classification

Run:
    uvicorn api:app --port 8000 --reload
"""
import os, sys, json, shutil, tempfile, glob as globmod, logging

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

    os.makedirs(OUT_DIR, exist_ok=True)

    path = os.path.join(OUT_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return {"saved": True, "path": path}


OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


@app.get("/api/history")
async def list_history():
    """List all saved classification results as summaries, newest first."""
    os.makedirs(OUT_DIR, exist_ok=True)
    items = []
    for path in globmod.glob(os.path.join(OUT_DIR, "*.json")):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            supplier = data.get("supplier") or {}
            items.append({
                "filename": os.path.basename(path),
                "document_file": data.get("document_file", ""),
                "document_type": data.get("document_type", ""),
                "date": data.get("date", ""),
                "supplier_name": supplier.get("name", ""),
                "total_amount": data.get("total_amount", 0),
                "confidence": data.get("confidence", ""),
                "branch": data.get("branch", ""),
                "saved_at": os.path.getmtime(path),
            })
        except Exception:
            continue
    items.sort(key=lambda x: x["saved_at"], reverse=True)
    return items


@app.get("/api/history/{filename}")
async def get_history(filename: str):
    """Load a single saved classification result."""
    path = os.path.join(OUT_DIR, filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@app.delete("/api/history/{filename}")
async def delete_history(filename: str):
    """Delete a saved classification result."""
    path = os.path.join(OUT_DIR, filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    os.remove(path)
    return {"deleted": True, "filename": filename}


# ── Chat agent ───────────────────────────────────────────────────────────────

_openai_client = None

def get_openai_client():
    global _openai_client
    if _openai_client is None:
        from dotenv import load_dotenv
        from openai import AzureOpenAI
        load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
        _openai_client = AzureOpenAI(
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version=os.environ["AZURE_OPENAI_API_VERSION"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        )
    return _openai_client


def _build_chat_system(classification: dict) -> str:
    rulebook_path = os.path.join(os.path.dirname(__file__), "RULEBOOK.md")
    rulebook = ""
    if os.path.isfile(rulebook_path):
        with open(rulebook_path, encoding="utf-8") as f:
            rulebook = f.read()

    # Strip agent_log from the context to save tokens
    ctx = {k: v for k, v in classification.items() if k != "agent_log"}

    return f"""You are a Greek accounting assistant helping a user review and correct a document classification.

You have access to the accounting rulebook and the current classification result.
Answer questions about why items were classified a certain way, explain the rules, and help fix errors.

When the user asks you to make a correction (move an item, change an account, fix an amount, etc.),
use the propose_classification_update tool to return the FULL corrected classification JSON.
Important rules for proposed updates:
- Include ALL fields: document_file, document_type, date, supplier, branch, total_amount, journal_entries, reasoning, confidence, flags
- Do NOT include agent_log in the proposed update
- Recalculate affected amounts: DR line amount = sum of its items' net_values; VAT amounts; CR total = invoice gross
- Make sure Σ DR = Σ CR in each entry

RULEBOOK:
{rulebook}

CURRENT CLASSIFICATION:
{json.dumps(ctx, ensure_ascii=False, indent=2)}
"""


CHAT_UPDATE_TOOL = {
    "type": "function",
    "function": {
        "name": "propose_classification_update",
        "description": (
            "Propose an updated classification with corrections applied. "
            "Return the FULL classification JSON (all fields except agent_log). "
            "The user will see an 'Apply changes' button to accept your corrections."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "updated_classification": {
                    "type": "object",
                    "description": "The full corrected ClassificationResult JSON"
                }
            },
            "required": ["updated_classification"]
        }
    }
}


@app.post("/api/chat")
async def chat(body: dict):
    """Multi-turn chat about a classification. Can propose edits via tool calling."""
    messages = body.get("messages", [])
    classification = body.get("classification", {})

    if not messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    client = get_openai_client()
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

    chat_messages = [
        {"role": "system", "content": _build_chat_system(classification)},
        *messages,
    ]

    try:
        response = client.chat.completions.create(
            model=deployment,
            messages=chat_messages,
            tools=[CHAT_UPDATE_TOOL],
            tool_choice="auto",
        )

        choice = response.choices[0]
        reply_text = (choice.message.content or "").strip()
        proposed_update = None

        # If the model called the tool, extract the proposed classification
        if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                if tc.function.name == "propose_classification_update":
                    args = json.loads(tc.function.arguments)
                    proposed_update = args.get("updated_classification")

            # If model produced no text alongside the tool call, make a follow-up call
            if not reply_text:
                chat_messages.append(choice.message)
                chat_messages.append({
                    "role": "tool",
                    "content": json.dumps({"status": "Changes prepared. Summarize what you changed."}),
                    "tool_call_id": choice.message.tool_calls[0].id,
                })
                follow_up = client.chat.completions.create(
                    model=deployment,
                    messages=chat_messages,
                )
                reply_text = (follow_up.choices[0].message.content or "").strip()

        return {"reply": reply_text, "proposed_update": proposed_update}

    except Exception as e:
        logging.exception("Chat error")
        raise HTTPException(status_code=500, detail=str(e))


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
