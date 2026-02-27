"""
CLASSIFICATION AGENT TEST RUNNER
==================================
Runs each test PDF through the agent and compares against the expected golden output.

Usage:
    cd _workspace
    python tests/run_tests.py                    # run all 5 tests
    python tests/run_tests.py TC1 TC3            # run specific tests
    python tests/run_tests.py --no-classify      # compare existing output/ files only

What is checked (STRICT):
  ✓ Correct number of journal entries
  ✓ Each entry is balanced (ΣDR = ΣCR, within 0.01)
  ✓ Correct account codes (exact match)
  ✓ Correct amounts (within 0.02 tolerance for rounding)
  ✓ CR total equals expected total_amount

What is NOT checked (advisory only):
  ~ Item descriptions (agent may paraphrase)
  ~ Reasoning text
  ~ Confidence level
"""
import os, sys, json, math

# Resolve paths relative to _workspace root
ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS    = os.path.dirname(os.path.abspath(__file__))
PDF_DIR  = os.path.join(TESTS, "pdfs")
EXP_DIR  = os.path.join(TESTS, "expected")
OUT_DIR  = os.path.join(ROOT, "output")

sys.path.insert(0, ROOT)

# ── Test case registry ────────────────────────────────────────────────────────

CASES = {
    "TC1": ("TC1_fuel_milos.pdf",        "TC1_fuel_milos.json"),
    "TC2": ("TC2_repair_mykonos.pdf",    "TC2_repair_mykonos.json"),
    "TC3": ("TC3_telecom_maroussi.pdf",  "TC3_telecom_maroussi.json"),
    "TC4": ("TC4_metro_food_only.pdf",   "TC4_metro_food_only.json"),
    "TC5": ("TC5_metro_mixed.pdf",       "TC5_metro_mixed.json"),
}

# ── Comparison logic ──────────────────────────────────────────────────────────

TOL = 0.02  # rounding tolerance on amounts

def near(a, b, tol=TOL):
    return abs(a - b) <= tol

def check_entry(got_entry, exp_entry, entry_idx):
    """Compare one journal entry. Returns list of (pass, message) tuples."""
    results = []

    got_lines = got_entry.get("lines", [])
    exp_lines = exp_entry.get("lines", [])

    # Balance check
    dr_sum = sum(l["amount"] for l in got_lines if l["side"] == "DR")
    cr_sum = sum(l["amount"] for l in got_lines if l["side"] == "CR")
    balanced = near(dr_sum, cr_sum, 0.01)
    results.append((balanced,
        f"  Entry {entry_idx}: balanced DR={dr_sum:.2f} CR={cr_sum:.2f}"
        + (" ✓" if balanced else f" ✗ (Δ={abs(dr_sum-cr_sum):.2f})")))

    # Account codes + amounts
    got_by_side = {}
    for l in got_lines:
        key = (l["side"], l["account"])
        got_by_side[key] = got_by_side.get(key, 0) + l["amount"]

    for exp_l in exp_lines:
        if exp_l.get("account","").startswith("_"):
            continue
        side    = exp_l["side"]
        account = exp_l["account"]
        exp_amt = exp_l["amount"]
        got_amt = got_by_side.get((side, account))

        if got_amt is None:
            # Check if any wrong account was used for this side/amount
            close_wrong = [(acc, amt) for (s, acc), amt in got_by_side.items()
                           if s == side and near(amt, exp_amt)]
            if close_wrong:
                wrong_acc, wrong_amt = close_wrong[0]
                results.append((False,
                    f"  Entry {entry_idx}: {side} {account} {exp_amt:.2f}"
                    f" ✗ — got wrong account {wrong_acc} instead"))
            else:
                results.append((False,
                    f"  Entry {entry_idx}: {side} {account} {exp_amt:.2f} ✗ — line MISSING"))
        else:
            ok = near(got_amt, exp_amt)
            results.append((ok,
                f"  Entry {entry_idx}: {side} {account} {exp_amt:.2f}"
                + (f" ✓" if ok else f" ✗ (got {got_amt:.2f}, diff {abs(got_amt-exp_amt):.2f})")))

    return results


def compare(got: dict, exp: dict, name: str):
    """Full comparison. Returns (pass_count, fail_count, messages)."""
    messages = []
    passes = fails = 0

    def record(ok, msg):
        nonlocal passes, fails
        messages.append(msg)
        if ok: passes += 1
        else:  fails  += 1

    # Supplier code
    got_code = got.get("supplier", {}).get("code", "")
    exp_code = exp.get("supplier", {}).get("code", "")
    ok = (got_code == exp_code)
    record(ok, f"  Supplier code: {exp_code}" + (" ✓" if ok else f" ✗ (got {got_code})"))

    # Total amount
    got_total = got.get("total_amount", 0)
    exp_total = exp.get("total_amount", 0)
    ok = near(got_total, exp_total)
    record(ok, f"  Total amount: {exp_total:.2f}" + (" ✓" if ok else f" ✗ (got {got_total:.2f})"))

    # Number of entries
    got_entries = got.get("journal_entries", [])
    exp_entries = exp.get("journal_entries", [])
    ok = (len(got_entries) == len(exp_entries))
    record(ok, f"  Entry count: {len(exp_entries)}" + (" ✓" if ok else f" ✗ (got {len(got_entries)})"))

    # Per-entry checks
    for i, exp_entry in enumerate(exp_entries):
        if i >= len(got_entries):
            record(False, f"  Entry {i+1}: MISSING")
            continue
        got_entry = got_entries[i]
        for ok, msg in check_entry(got_entry, exp_entry, i+1):
            record(ok, msg)

    # Item count (advisory)
    exp_item_count = exp.get("_checks", {}).get("item_count")
    if exp_item_count is not None:
        got_items = sum(
            len(l.get("items", []))
            for e in got_entries
            for l in e.get("lines", [])
        )
        ok = (got_items >= exp_item_count)
        msg = f"  Items extracted: {exp_item_count} expected, got {got_items}"
        msg += " ✓" if ok else f" ✗ ({exp_item_count - got_items} missing)"
        messages.append("[items] " + msg)  # advisory — doesn't count as fail

    return passes, fails, messages


# ── Runner ────────────────────────────────────────────────────────────────────

def run_case(name, pdf_file, exp_file, classify=True):
    print(f"\n{'─'*60}")
    print(f"  {name}  |  {pdf_file}")
    print(f"{'─'*60}")

    exp_path = os.path.join(EXP_DIR, exp_file)
    with open(exp_path, encoding="utf-8") as f:
        expected = json.load(f)
    print(f"  Difficulty: {expected.get('_difficulty','?').upper()}")
    print(f"  {expected.get('_note','')}")

    # Classify or load cached result
    if classify:
        pdf_path = os.path.join(PDF_DIR, pdf_file)
        if not os.path.exists(pdf_path):
            print(f"  ✗ PDF not found: {pdf_path}")
            print(f"    → Run: python tests/generate_test_pdfs.py")
            return 0, 1

        print(f"  → Classifying (this takes 15-40s)...")
        import agent as ag
        result = ag.classify(pdf_path)
        # save to output/
        out_path = os.path.join(OUT_DIR, pdf_file.replace(".pdf", ".json"))
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  → Saved: output/{pdf_file.replace('.pdf','.json')}")
    else:
        stem = pdf_file.replace(".pdf", ".json")
        out_path = os.path.join(OUT_DIR, stem)
        if not os.path.exists(out_path):
            print(f"  ✗ No cached output at {out_path}. Re-run without --no-classify.")
            return 0, 1
        with open(out_path, encoding="utf-8") as f:
            result = json.load(f)
        print(f"  → Using cached: output/{stem}")

    passes, fails, messages = compare(result, expected, name)

    print()
    for msg in messages:
        print(msg)

    verdict = "PASS" if fails == 0 else "FAIL"
    print(f"\n  {'✓ PASS' if fails == 0 else '✗ FAIL'}  ({passes} passed, {fails} failed)")
    return passes, fails


def main():
    args = sys.argv[1:]
    no_classify = "--no-classify" in args
    args = [a for a in args if not a.startswith("--")]

    if args:
        selected = {k: v for k, v in CASES.items() if k in args}
    else:
        selected = CASES

    if not selected:
        print(f"Unknown test case(s). Available: {', '.join(CASES)}")
        sys.exit(1)

    total_pass = total_fail = 0
    for name, (pdf, exp) in selected.items():
        p, f = run_case(name, pdf, exp, classify=not no_classify)
        total_pass += p
        total_fail += f

    print(f"\n{'='*60}")
    print(f"  TOTAL: {total_pass} passed, {total_fail} failed")
    if total_fail == 0:
        print("  ALL TESTS PASSED ✓")
    else:
        print(f"  {total_fail} CHECK(S) FAILED ✗")
    print(f"{'='*60}")
    sys.exit(0 if total_fail == 0 else 1)


if __name__ == "__main__":
    main()
