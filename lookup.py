"""
CLASSIFICATION LOOKUP TOOL
===========================
Usage (interactive or imported):
  python lookup.py supplier <afm>
  python lookup.py supplier_name <keyword>
  python lookup.py account <code>
  python lookup.py accounts <subgroup>          e.g. 62.07
  python lookup.py find_account <keyword>       e.g. ΚΑΥΣΙΜΑ or ΚΕΡΚΥΡΑ
  python lookup.py classify                     # interactive mode
"""
import json, os, sys, re, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")

def load(fname):
    path = os.path.join(DATA, fname)
    with open(path, encoding='utf-8') as f:
        return json.load(f)

# ── Lazy loaders ─────────────────────────────────────────────────────────────
_accounts = None
_by_afm = None
_by_code = None
_by_name = None
_by_subgroup = None
_by_keyword = None

def accounts():
    global _accounts
    if _accounts is None: _accounts = load("accounts.json")
    return _accounts

def suppliers_by_afm():
    global _by_afm
    if _by_afm is None: _by_afm = load("suppliers_by_afm.json")
    return _by_afm

def suppliers_by_code():
    global _by_code
    if _by_code is None: _by_code = load("suppliers_by_code.json")
    return _by_code

def suppliers_by_name():
    global _by_name
    if _by_name is None: _by_name = load("suppliers_by_name.json")
    return _by_name

def accounts_by_subgroup():
    global _by_subgroup
    if _by_subgroup is None: _by_subgroup = load("accounts_by_subgroup.json")
    return _by_subgroup

def accounts_by_keyword():
    global _by_keyword
    if _by_keyword is None: _by_keyword = load("accounts_by_keyword.json")
    return _by_keyword

# ── Core lookup functions ─────────────────────────────────────────────────────

def get_supplier_by_afm(afm: str) -> dict | None:
    """Look up supplier by exact AFM."""
    return suppliers_by_afm().get(afm.strip())

def search_suppliers_by_name(keyword: str, max_results=10) -> list:
    """Fuzzy search suppliers by name keyword."""
    kw = re.sub(r'[^Α-ΩA-Z0-9]', '', keyword.upper())
    idx = suppliers_by_name()
    results = idx.get(kw, [])
    # Also search all keys for partial match
    if not results:
        for key in idx:
            if kw in key or key in kw:
                results.extend(idx[key])
    # Deduplicate by code
    seen = set()
    out = []
    for r in results:
        if r['code'] not in seen:
            seen.add(r['code'])
            out.append(r)
        if len(out) >= max_results:
            break
    return out

def get_account(code: str) -> dict | None:
    """Look up account by exact code."""
    return accounts().get(code.strip())

def list_accounts_for(subgroup: str) -> list:
    """List all accounts under a subgroup (e.g. '62.07', '64.00')."""
    sg = accounts_by_subgroup()
    entries = sg.get(subgroup, [])
    # Only return detail-level (3-part) codes
    return [e for e in entries if e['code'].count('.') == 2]

def find_accounts_by_description(keyword: str, max_results=15) -> list:
    """Search accounts by description keyword."""
    kw = re.sub(r'[^Α-ΩA-Z0-9]', '', keyword.upper())
    idx = accounts_by_keyword()
    results = idx.get(kw, [])
    # Partial key search
    if not results:
        for key in idx:
            if kw in key or key in kw:
                results.extend(idx[key])
    seen = set()
    out = []
    for r in results:
        if r['code'] not in seen:
            seen.add(r['code'])
            out.append(r)
        if len(out) >= max_results:
            break
    return out

def find_best_account(subgroup: str, branch_hint: str = '', vat_hint: str = '') -> list:
    """
    For a given subgroup (e.g. '62.07') and optional hints,
    return the most likely account codes.
    - branch_hint: e.g. 'ΚΕΡΚΥΡΑ', 'ΑΔΑΜΑΝΤΑΣ', 'ΚΕΝΤΡΙΚΟ'
    - vat_hint: e.g. '24', '13', '6', '0'
    """
    candidates = list_accounts_for(subgroup)
    scored = []
    bh = branch_hint.upper()
    vh = vat_hint.replace('%', '')

    for c in candidates:
        score = 0
        desc_upper = c['desc'].upper()
        if bh and bh in desc_upper:
            score += 10
        if vh:
            if c['code'].endswith(vh):
                score += 5
            if vh == '0' and c['code'].endswith('00'):
                score += 5
        if 'ΑΝΕΥ' in desc_upper and (vh in ('0', '00', '')):
            score += 2
        scored.append((score, c))

    scored.sort(key=lambda x: -x[0])
    return [(s, c) for s, c in scored if s > 0 or not branch_hint]

# ── VAT routing rules ─────────────────────────────────────────────────────────

VAT_ROUTING = {
    # expense_subgroup → vat_account_subgroup
    "62.03": "54.00",   # telecom → 54.00.62024
    "62.04": None,      # rents → no VAT (or special)
    "62.05": None,      # insurance → no VAT
    "62.07": "54.00",   # repairs → 54.00.62024
    "62.98": "54.00",   # utilities → 54.00.62006 / 54.00.62024
    "61.00": "54.00",   # professional fees → 54.00.61024
    "61.98": "54.00",   # leasing → 54.00.62024
    "64.00": "54.00",   # fuel → 54.00.64024
    "64.07": "54.00",   # stationery → 54.00.64024
    "64.08": "54.00",   # cleaning → 54.00.64024 (but food@METRO → 63.98!)
    "64.98": "54.00",   # misc expenses → 54.00.64024
    "65.98": None,      # banking fees → no VAT (or 54.00.64024 on fees)
    "60.02": "63.98",   # canteen/food → NON-DEDUCTIBLE 63.98.00813/824
}

def vat_account(expense_subgroup: str, vat_rate: str, is_food: bool = False) -> str | None:
    """
    Given an expense account subgroup and VAT rate, return the correct VAT account code.
    is_food: True for canteen/food items (routes to 63.98 non-deductible)
    """
    if is_food:
        if vat_rate in ('13', '13%'):
            return "63.98.00813"
        if vat_rate in ('24', '24%'):
            return "63.98.00824"
    routing = VAT_ROUTING.get(expense_subgroup)
    if routing is None:
        return None  # no VAT account needed
    if routing == "54.00":
        # Determine which 54.00 sub-account
        sg_short = expense_subgroup.split('.')[1]  # e.g. '07' from '62.07'
        group = expense_subgroup.split('.')[0]     # e.g. '62'
        vr = vat_rate.replace('%', '').zfill(3)  # pad to 3 digits: '24' → '024'
        if group == '62':
            return f"54.00.62{vr}"
        elif group == '61':
            return f"54.00.61{vr}"
        elif group in ('64', '65'):
            return f"54.00.64{vr}"
    return None

# ── CLI ───────────────────────────────────────────────────────────────────────

def print_results(results, title=''):
    if title:
        print(f"\n{'='*50}")
        print(f" {title}")
        print(f"{'='*50}")
    if not results:
        print("  (no results)")
        return
    for r in results:
        if isinstance(r, tuple):
            score, item = r
            print(f"  [{score:2d}] {item['code']:25} {item['desc']}")
        elif isinstance(r, dict):
            code = r.get('code', '')
            name = r.get('name', r.get('desc', ''))
            afm  = r.get('afm', '')
            city = r.get('city', '')
            print(f"  {code:25} {name[:40]:40} AFM:{afm:12} {city}")

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return

    cmd = args[0].lower()

    if cmd == 'supplier' and len(args) > 1:
        r = get_supplier_by_afm(args[1])
        if r:
            print(f"\nSupplier: {r['name']}")
            print(f"  Code : {r['code']}")
            print(f"  AFM  : {r['afm']}")
            print(f"  Addr : {r['addr']}, {r['city']}")
        else:
            print("Not found.")

    elif cmd == 'supplier_name' and len(args) > 1:
        results = search_suppliers_by_name(' '.join(args[1:]))
        print_results(results, f"Suppliers matching '{' '.join(args[1:])}'")

    elif cmd == 'account' and len(args) > 1:
        r = get_account(args[1])
        if r:
            print(f"\n{args[1]}: {r['desc']}")
            print(f"  Group: {r['group']}  Subgroup: {r['subgroup']}")
        else:
            print("Not found.")

    elif cmd == 'accounts' and len(args) > 1:
        results = list_accounts_for(args[1])
        print_results(results, f"All accounts under {args[1]}")

    elif cmd == 'find_account' and len(args) > 1:
        kw = ' '.join(args[1:])
        results = find_accounts_by_description(kw)
        print_results(results, f"Accounts matching '{kw}'")

    elif cmd == 'best_account' and len(args) > 1:
        subgroup = args[1]
        branch = args[2] if len(args) > 2 else ''
        vat = args[3] if len(args) > 3 else ''
        results = find_best_account(subgroup, branch, vat)
        print_results(results[:8], f"Best accounts for {subgroup} / branch={branch} / vat={vat}%")

    elif cmd == 'vat' and len(args) > 2:
        acc = vat_account(args[1], args[2])
        print(f"VAT account for {args[1]} @{args[2]}%: {acc}")

    else:
        print(__doc__)

if __name__ == '__main__':
    main()
