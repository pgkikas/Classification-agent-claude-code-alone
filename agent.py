"""
ACCOUNTING CLASSIFICATION AGENT
================================
Classifies PDF documents into Greek accounting journal entries.
Uses Azure OpenAI (vision + tool calling) + lookup.py tools.

Usage:
    python agent.py <pdf_path>
    python agent.py ../pdfs/named/ΜΕΤΡΟ.pdf
    python agent.py ../pdfs/sdoc/SDOC25121710050.pdf
"""
import os, sys, json, base64, io, logging
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import fitz
from dotenv import load_dotenv
from openai import AzureOpenAI

# ── Logging setup ─────────────────────────────────────────────────────────────

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

_handler_stdout = logging.StreamHandler(sys.stdout)
_handler_file   = logging.FileHandler(os.path.join(LOG_DIR, "agent.log"), encoding="utf-8")
_formatter      = logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s", datefmt="%H:%M:%S")
_handler_stdout.setFormatter(_formatter)
_handler_file.setFormatter(_formatter)

# Root logger at WARNING — silences noisy third-party libraries (openai, httpx, etc.)
logging.getLogger().setLevel(logging.WARNING)

# Our agent logger at DEBUG — shows everything we explicitly log
log = logging.getLogger("agent")
log.setLevel(logging.DEBUG)
log.propagate = False          # don't pass up to root
log.addHandler(_handler_stdout)
log.addHandler(_handler_file)

# Load lookup functions from same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lookup as lk

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# ── Azure OpenAI client ───────────────────────────────────────────────────────

client = AzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
)
DEPLOYMENT = os.environ["AZURE_OPENAI_DEPLOYMENT"]

# ── PDF → base64 images ───────────────────────────────────────────────────────

def pdf_to_images(pdf_path: str) -> list[str]:
    """Convert each page of a PDF to a base64-encoded PNG string."""
    log.info(f"PDF → images  |  file: {os.path.basename(pdf_path)}")
    doc = fitz.open(pdf_path)
    images = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        png_bytes = pix.tobytes("png")
        kb = len(png_bytes) // 1024
        images.append(base64.b64encode(png_bytes).decode("utf-8"))
        log.debug(f"  page {i+1}: {pix.width}x{pix.height}px  ({kb} KB)")
    doc.close()
    log.info(f"  extracted {len(images)} page(s)")
    return images

# ── Tool definitions (OpenAI function-calling format) ────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_supplier_by_afm",
            "description": (
                "Look up a supplier by their Greek tax ID (ΑΦΜ). "
                "This is the primary identification method — always try this first "
                "when you can read an ΑΦΜ from the document."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "afm": {
                        "type": "string",
                        "description": "The supplier's ΑΦΜ (9-digit Greek tax ID)"
                    }
                },
                "required": ["afm"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_supplier_by_name",
            "description": (
                "Search for a supplier by name keyword when the ΑΦΜ is unclear or missing. "
                "Returns up to 10 matching suppliers with their codes and ΑΦΜ."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "A keyword from the supplier name (e.g. 'ΜΕΤΡΟ', 'CORAL', 'ICAR')"
                    }
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_best_account",
            "description": (
                "Find the best matching account code for a given subgroup, branch, and VAT rate. "
                "Returns scored candidates — the highest score is the best match. "
                "Always verify the description matches the expense type."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "subgroup": {
                        "type": "string",
                        "description": "Account subgroup, e.g. '62.07', '64.00', '60.02', '64.08'"
                    },
                    "branch": {
                        "type": "string",
                        "description": "Branch name hint, e.g. 'ΚΕΝΤΡΙΚΟ', 'ΚΕΡΚΥΡΑ', 'ΑΔΑΜΑΝΤΑΣ', 'ΜΑΡΟΥΣΙ'"
                    },
                    "vat_rate": {
                        "type": "string",
                        "description": "VAT rate as string, e.g. '24', '13', '6', '0'"
                    }
                },
                "required": ["subgroup"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_accounts_for_subgroup",
            "description": (
                "List all account codes under a subgroup. "
                "Useful for browsing available codes when unsure of the exact branch."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "subgroup": {
                        "type": "string",
                        "description": "Account subgroup, e.g. '62.07', '64.00', '63.03', '38.03'"
                    }
                },
                "required": ["subgroup"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_accounts_by_keyword",
            "description": (
                "Search account codes by Greek keyword in their description. "
                "Useful when you know a location name or expense type but not the subgroup."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Greek keyword to search, e.g. 'ΚΕΡΚΥΡΑ', 'ΚΑΥΣΙΜΑ', 'ΤΗΝΟΣ'"
                    }
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_vat_account",
            "description": (
                "Get the correct VAT account code for a given expense subgroup and VAT rate. "
                "Handles the critical food/canteen exception (non-deductible VAT → 63.98)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expense_subgroup": {
                        "type": "string",
                        "description": "The expense account subgroup, e.g. '62.07', '64.00', '60.02'"
                    },
                    "vat_rate": {
                        "type": "string",
                        "description": "VAT rate as string, e.g. '24', '13', '6'"
                    },
                    "is_food": {
                        "type": "boolean",
                        "description": "True for food/canteen items (routes to non-deductible 63.98)"
                    }
                },
                "required": ["expense_subgroup", "vat_rate"]
            }
        }
    },
]

# ── Tool executor ─────────────────────────────────────────────────────────────

def execute_tool(name: str, args: dict) -> str:
    """Execute a tool call and return the result as a JSON string."""
    log.debug(f"  TOOL CALL  →  {name}({args})")
    try:
        if name == "lookup_supplier_by_afm":
            result = lk.get_supplier_by_afm(args["afm"])
            if result:
                log.debug(f"  TOOL RESULT →  found: {result['name']}  code: {result['code']}")
                return json.dumps(result, ensure_ascii=False)
            log.warning(f"  TOOL RESULT →  AFM {args['afm']} NOT FOUND in supplier archive")
            return json.dumps({"error": f"Supplier with AFM {args['afm']} not found in archive"})

        elif name == "search_supplier_by_name":
            results = lk.search_suppliers_by_name(args["keyword"])
            log.debug(f"  TOOL RESULT →  {len(results)} supplier(s) matched")
            for r in results[:3]:
                log.debug(f"    {r['code']}  {r['name']}  AFM:{r['afm']}")
            return json.dumps(results, ensure_ascii=False)

        elif name == "find_best_account":
            results = lk.find_best_account(
                args["subgroup"],
                args.get("branch", ""),
                args.get("vat_rate", "")
            )
            out = [{"score": s, "code": c["code"], "desc": c["desc"]} for s, c in results[:8]]
            log.debug(f"  TOOL RESULT →  top match: {out[0]['code']} [{out[0]['score']}] {out[0]['desc']}" if out else "  TOOL RESULT →  no matches")
            return json.dumps(out, ensure_ascii=False)

        elif name == "list_accounts_for_subgroup":
            results = lk.list_accounts_for(args["subgroup"])
            log.debug(f"  TOOL RESULT →  {len(results)} account(s) under {args['subgroup']}")
            for r in results[:5]:
                log.debug(f"    {r['code']}  {r['desc']}")
            return json.dumps(results, ensure_ascii=False)

        elif name == "find_accounts_by_keyword":
            results = lk.find_accounts_by_description(args["keyword"])
            log.debug(f"  TOOL RESULT →  {len(results)} account(s) matched keyword '{args['keyword']}'")
            for r in results[:3]:
                log.debug(f"    {r['code']}  {r['desc']}")
            return json.dumps(results, ensure_ascii=False)

        elif name == "get_vat_account":
            result = lk.vat_account(
                args["expense_subgroup"],
                args["vat_rate"],
                args.get("is_food", False)
            )
            log.debug(f"  TOOL RESULT →  VAT account: {result}")
            return json.dumps({"vat_account": result}, ensure_ascii=False)

        else:
            log.error(f"  TOOL ERROR  →  unknown tool: {name}")
            return json.dumps({"error": f"Unknown tool: {name}"})

    except Exception as e:
        log.error(f"  TOOL ERROR  →  {name} raised: {e}")
        return json.dumps({"error": str(e)})

# ── System prompt ─────────────────────────────────────────────────────────────

def build_system_prompt() -> str:
    rulebook_path = os.path.join(os.path.dirname(__file__), "RULEBOOK.md")
    with open(rulebook_path, encoding="utf-8") as f:
        rulebook = f.read()

    return f"""You are a Greek accounting classification agent for ΠΡΟΠΟΡΕΙΑ Α.Ε. (Avance Rent A Car, ΑΦΜ: 095600200).

Your job is to read a document image and produce the correct accounting journal entries using the tools provided.

{rulebook}

---

## HOW TO WORK — follow these steps in order:

STEP 1: Read the document carefully.
  - Identify: document type (invoice/ΤΠΥ/ΤΔΑ, bank payment confirmation, receipt/απόδειξη)
  - Extract: supplier name, ΑΦΜ, date, branch/location clues
  - Number and list EVERY individual line item visible on the invoice body (1, 2, 3...):
    description, quantity, unit, unit price, net value, VAT rate %, VAT amount, gross value.
    After listing, state explicitly: "I found N line items in total."
  ⚠ WARNING — VAT SUMMARY TABLE TRAP:
    Invoices print a VAT summary at the bottom (e.g. "Σύνολο 13%: 90.95 | 24%: 28.24 | 6%: 2.68").
    These totals are COMBINED across ALL expense categories.
    A single VAT rate row (e.g. 24%) can contain BOTH food items AND cleaning items.
    NEVER use a VAT summary row amount as a DR line amount — amounts MUST be derived by summing items.

STEP 2: Identify the supplier.
  - If you can read an ΑΦΜ → call lookup_supplier_by_afm first (most reliable)
  - If ΑΦΜ is unclear → call search_supplier_by_name
  - Get the supplier's 50.xx ledger code

STEP 3: Categorise each line item and compute per-category amounts.
  - For EACH item from the list in STEP 1, assign a category:
      food/canteen → 60.02  (coffee, water, dairy, beverages, sugar, honey,
                              kitchen consumables: non-stick/baking paper, espresso equipment,
                              shopping bags purchased alongside food items,
                              any item whose primary use is in food preparation or serving)
      cleaning     → 64.08  (detergents, disinfectants, hygiene products, clothespins,
                              industrial paper rolls for cleaning surfaces or wrapping in service,
                              mops/cloths/gloves and other pure cleaning consumables)
      ⚠ BORDERLINE ITEMS: if an item could be either canteen or cleaning, look at the invoice
        context. If the invoice is from a food/catering supplier and the item accompanies food
        products, assign it to food/canteen (60.02). If it is a standalone cleaning product or
        the invoice is from a cleaning supplier, assign it to cleaning (64.08).
      fuel         → 64.00  |  repairs → 62.07  |  telecom → 62.03  |  other → 64.98
  - Group items by (category, VAT rate) and SUM their net_values.
    These sums become the DR expense line amounts — derived from items, NOT from the VAT summary table.
    All groups go into ONE single journal entry (see JOURNAL ENTRY STRUCTURE RULES):
      category A @VAT1 net = Σ(items in cat A with VAT1) → DR <account A>  /  VAT → <VAT account>
      category A @VAT2 net = Σ(items in cat A with VAT2) → DR <account A>  /  VAT → <VAT account>
      category B @VAT1 net = Σ(items in cat B with VAT1) → DR <account B>  /  VAT → <VAT account>
      CR supplier = FULL invoice gross total  ← ONE single CR for the entire invoice
  ⚠ ITEMS ARE THE SOURCE OF TRUTH FOR AMOUNTS:
    DR line amount = sum of its items' net_values. If your sum disagrees with the VAT summary,
    trust your item sum — the summary combines categories. If they agree, great.
  - Verify: total items across all groups = N from Step 1. If count is off, you skipped items.
  - Verify: Σ(all category nets + VATs) = invoice total. If not, re-read items.

STEP 4: Find the exact account code.
  - Call find_best_account(subgroup, branch, vat_rate)
  - Verify the returned description matches the expense
  - If uncertain, also call list_accounts_for_subgroup to browse all options

STEP 5: Determine the VAT account.
  - Call get_vat_account(expense_subgroup, vat_rate)
  - CRITICAL: food/canteen → is_food=true → routes to 63.98 (NON-DEDUCTIBLE)

STEP 6: Build the journal entries.
  - ONE ENTRY per invoice per supplier — even if the invoice spans multiple expense categories or VAT rates.
    Within the single entry:
      • DR expense line for each (category × VAT rate) group (from STEP 3)
      • DR VAT line for each group (from STEP 5)
      • ONE single CR to the supplier for the FULL invoice gross total
  - BANK PAYMENT (state/tax): DR expense  /  CR bank 38.03.00009
  - BANK PAYMENT (to supplier): DR supplier 50.xx  /  CR bank 38.03.00009
  - Exception: use multiple entries ONLY when there are genuinely distinct payees in the same
    document (e.g. a bank statement that charges both a state tax and a bank service fee as
    separate line items to different accounts — those are separate entries because the CR targets differ).
  - Verify the entire entry: Σ all DR lines = Σ all CR lines

---

## STRICT RULES:
- ALWAYS use tools to look up codes. NEVER invent or guess account codes.
- NEVER use DOCUMENT_LOG or any cheat sheet — derive everything from the rulebook and tools.
- Always verify: debit total must equal credit total per entry.
- NEVER copy a VAT summary row amount directly into a DR line — always derive from categorized items.

---

## OUTPUT FORMAT:
After completing all tool calls, output ONLY valid JSON in exactly this structure:

{{
  "document_file": "<filename>",
  "document_type": "invoice|bank_payment|receipt",
  "date": "<dd/mm/yyyy>",
  "supplier": {{"name": "<name>", "afm": "<afm>", "code": "<50.xx.xxxxx>"}},
  "branch": "<branch name or ΚΕΝΤΡΙΚΟ>",
  "total_amount": 0.00,
  "journal_entries": [
    {{
      "entry": 1,
      "description": "<brief description>",
      "lines": [
        {{
          "side": "DR",
          "account": "<expense account code>",
          "description": "<desc>",
          "amount": 0.00,
          "items": [
            {{
              "description": "<exact item description from the invoice>",
              "quantity": 0.00,
              "unit": "<τεμ|kg|lt — blank if not stated>",
              "unit_price": 0.00,
              "net_value": 0.00,
              "vat_rate": 0,
              "vat_amount": 0.00,
              "gross_value": 0.00,
              "category": "<food|cleaning|fuel|office|repair|vehicle|telecom|other>"
            }}
          ]
        }},
        {{"side": "DR", "account": "<VAT account 54.xx or 63.98>", "description": "<desc>", "amount": 0.00, "items": []}},
        {{"side": "CR", "account": "<supplier or bank>",           "description": "<desc>", "amount": 0.00, "items": []}}
      ]
    }}
  ],
  "reasoning": "<step-by-step explanation of every decision>",
  "confidence": "high|medium|low",
  "flags": ["<any uncertainties or items needing accountant review>"]
}}

## JOURNAL ENTRY STRUCTURE RULES:

1. ONE entry per invoice per supplier — regardless of how many expense categories or VAT rates appear.
   Within that single entry:
   - Separate DR expense lines for each (category × VAT rate) combination.
   - Separate DR VAT lines for each (category × VAT rate) combination.
   - ONE single CR line to the supplier = the FULL gross total of the entire invoice.
   Exception: multiple entries only when the document contains genuinely distinct payees
   (e.g. a bank-issued document that separately charges a state tax and a bank service fee
   → two entries because the DR accounts and purpose are categorically different).

2. ⚠ NEVER split the CR by category or VAT rate:
   CR 50.00.xxxxx  <supplier>  <full invoice gross>   ← single CR, always the full total
   DR ...  category A @ VAT rate 1
   DR ...  VAT on category A
   DR ...  category B @ VAT rate 2
   DR ...  VAT on category B
   All DR lines together must equal the one CR line. That is your balance check.

## ITEMS ARRAY RULES — items are nested inside each DR EXPENSE line:

- Each DR expense line (60.xx, 62.xx, 63.98, 64.xx, 65.xx) has an "items" array containing
  the individual invoice product lines that make up that line's amount.
- VAT lines (54.00.xx) and CR lines (50.xx, 38.xx) always have items: [].
- One DR expense line per (category × VAT rate), so all items in a line share the same VAT rate.
- COMPLETENESS: Every product line from the invoice body MUST appear in exactly one items[] array.
  If the invoice has 13 food@13% items, the DR 60.02 @13% line must contain all 13 — not a sample.
  Do NOT summarise, group, or omit items. One invoice line = one items[] entry.
- AMOUNTS COME FROM ITEMS, NOT THE SUMMARY TABLE:
  The DR line amount field = sum(items[].net_value). Set the amount AFTER you have listed all items.
  Never set the amount first and then list partial items to justify it.
- For bank payments and documents with no itemised list, all lines have items: [].
- Category values: food (groceries/beverages/canteen), cleaning (hygiene/cleaning products),
  fuel (petrol/diesel/LPG), office (stationery/printing), repair (maintenance/parts),
  vehicle (tyres/insurance/road tax), telecom (phone/internet), other (anything else).
- FINAL CHECK: Count total items in your JSON output. Must equal N from Step 1.
  If count is lower, you omitted items — go back and add them before finishing.
"""

# ── Agent loop ────────────────────────────────────────────────────────────────

def classify(pdf_path: str) -> dict:
    """Run the full classification pipeline on a PDF. Returns parsed result dict."""
    pdf_path = os.path.abspath(pdf_path)
    filename = os.path.basename(pdf_path)

    log.info(f"{'='*60}")
    log.info(f"Classifying: {filename}")
    log.info(f"{'='*60}")

    # Convert PDF to images
    images = pdf_to_images(pdf_path)

    # Build initial message with all pages
    image_content = []
    for i, img_b64 in enumerate(images):
        image_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{img_b64}",
                "detail": "high"
            }
        })
    image_content.append({
        "type": "text",
        "text": f"Classify this document (file: {filename}). Follow the 6-step process. Use tools to look up all account codes and suppliers."
    })

    messages = [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user", "content": image_content}
    ]

    # Agentic tool-calling loop
    log.info("Starting agent loop")
    tool_call_count = 0
    gpt_call_count  = 0
    agent_log = []  # structured trace of every step

    while True:
        gpt_call_count += 1
        log.info(f"GPT call #{gpt_call_count}  |  messages in context: {len(messages)}")

        response = client.chat.completions.create(
            model=DEPLOYMENT,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        choice = response.choices[0]
        usage  = response.usage
        log.info(
            f"GPT call #{gpt_call_count} response  |  "
            f"finish_reason: {choice.finish_reason}  |  "
            f"tokens: prompt={usage.prompt_tokens}  completion={usage.completion_tokens}  total={usage.total_tokens}"
        )

        # Capture any text reasoning the model produced this turn
        reasoning_text = (choice.message.content or "").strip()
        if reasoning_text:
            log.info(f"  LLM reasoning:\n{reasoning_text[:500]}{'...' if len(reasoning_text) > 500 else ''}")

        # Handle tool calls
        if choice.finish_reason == "tool_calls":
            messages.append(choice.message)

            step_tools = []
            for tc in choice.message.tool_calls:
                tool_call_count += 1
                log.info(f"--- Tool call {tool_call_count}: {tc.function.name} ---")
                args = json.loads(tc.function.arguments)
                result = execute_tool(tc.function.name, args)
                messages.append({
                    "role": "tool",
                    "content": result,
                    "tool_call_id": tc.id
                })
                # Summarise result for the log (truncate long lists)
                try:
                    parsed = json.loads(result)
                    if isinstance(parsed, list) and len(parsed) > 3:
                        result_summary = json.dumps(parsed[:3], ensure_ascii=False) + f" ... ({len(parsed)} total)"
                    else:
                        result_summary = result if len(result) <= 300 else result[:300] + "..."
                except Exception:
                    result_summary = result[:300] if len(result) > 300 else result

                step_tools.append({
                    "name": tc.function.name,
                    "args": args,
                    "result": result_summary,
                })

            agent_log.append({
                "step": gpt_call_count,
                "reasoning": reasoning_text or None,
                "tool_calls": step_tools,
                "tokens": {
                    "prompt": usage.prompt_tokens,
                    "completion": usage.completion_tokens,
                    "total": usage.total_tokens,
                },
            })
        else:
            # Final answer
            raw = choice.message.content.strip()
            agent_log.append({
                "step": gpt_call_count,
                "reasoning": "Final JSON output produced.",
                "tool_calls": [],
                "tokens": {
                    "prompt": usage.prompt_tokens,
                    "completion": usage.completion_tokens,
                    "total": usage.total_tokens,
                },
            })
            log.info(f"Agent finished  |  {gpt_call_count} GPT call(s), {tool_call_count} tool call(s)")
            break

    # Parse JSON output
    log.info("Parsing structured JSON output...")
    try:
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
    except json.JSONDecodeError:
        result = {"raw_output": raw, "parse_error": "Could not parse JSON"}

    # Attach the agent trace so the UI can display it
    result["agent_log"] = agent_log

    return result

# ── Output formatting ─────────────────────────────────────────────────────────

def print_result(result: dict):
    """Pretty-print the classification result to terminal."""
    if "parse_error" in result:
        print("\n  [!] Could not parse structured output. Raw response:")
        print(result.get("raw_output", ""))
        return

    print(f"\n{'='*60}")
    print(f" RESULT")
    print(f"{'='*60}")
    print(f"  Document : {result.get('document_file', '?')}")
    print(f"  Type     : {result.get('document_type', '?')}")
    print(f"  Date     : {result.get('date', '?')}")
    sup = result.get('supplier', {})
    print(f"  Supplier : {sup.get('name', '?')}  |  ΑΦΜ: {sup.get('afm', '?')}  |  Code: {sup.get('code', '?')}")
    print(f"  Branch   : {result.get('branch', '?')}")
    print(f"  Total    : {result.get('total_amount', '?')} EUR")
    print(f"  Confidence: {result.get('confidence', '?').upper()}")

    for entry in result.get("journal_entries", []):
        print(f"\n  --- Entry {entry.get('entry', '?')}: {entry.get('description', '')} ---")
        print(f"  {'Side':<5} {'Account':<25} {'Description':<35} {'Amount':>10}")
        print(f"  {'-'*80}")
        for line in entry.get("lines", []):
            print(f"  {line['side']:<5} {line['account']:<25} {line['description'][:35]:<35} {line['amount']:>10.2f}")

    if result.get("flags"):
        print(f"\n  [!] FLAGS:")
        for f in result["flags"]:
            print(f"      - {f}")

    print(f"\n  REASONING:")
    for line in result.get("reasoning", "").split("\n"):
        if line.strip():
            print(f"    {line}")

def save_result(result: dict, pdf_path: str):
    """Save result JSON to _workspace/output/<name>.json"""
    out_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(pdf_path))[0]
    out_path = os.path.join(out_dir, f"{stem}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    log.info(f"Result saved → output/{stem}.json")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python agent.py <pdf_path>")
        print("       python agent.py ../pdfs/named/ΜΕΤΡΟ.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"Error: file not found: {pdf_path}")
        sys.exit(1)

    result = classify(pdf_path)
    print_result(result)
    save_result(result, pdf_path)

if __name__ == "__main__":
    main()
