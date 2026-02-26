# AVANCE RENT A CAR — Document Classification Workspace
### ΠΡΟΠΟΡΕΙΑ Α.Ε. | ΑΦΜ: 095600200

---

## What This Is

This workspace is the knowledge base and toolset for classifying accounting documents
(invoices, receipts, bank payments) into journal entries using the company's
chart of accounts and supplier archive.

---

## Folder Structure

```
_workspace/
│
├── README.md              ← you are here
│
├── RULEBOOK.md            ← HOW TO CLASSIFY: account taxonomy, decision tree,
│                             VAT routing rules, and 5 ground-truth examples
│
├── DOCUMENT_LOG.md        ← RESULTS: all 35 PDFs classified with journal entries
│
├── lookup.py              ← TOOL: search accounts and suppliers from command line
│
├── build_indexes.py       ← MAINTENANCE: re-runs if Excel source files change
│
└── data/                  ← RAW DATA (auto-generated, do not edit manually)
    ├── accounts.json               637 account codes from chart of accounts
    ├── accounts_by_subgroup.json   accounts grouped by category (62.07, 64.00 etc.)
    ├── accounts_by_keyword.json    keyword search index (Greek text → account)
    ├── suppliers_by_afm.json       6,293 suppliers indexed by tax ID (ΑΦΜ)  ← primary
    ├── suppliers_by_code.json      6,322 suppliers indexed by ledger code (50.xx)
    └── suppliers_by_name.json      keyword search index (name → supplier)
```

---

## How to Use the Lookup Tool

Open a terminal in this folder and run:

```bash
# Find a supplier by their tax ID (ΑΦΜ — always on the invoice)
python lookup.py supplier 094062259

# Search a supplier by name when ΑΦΜ is unclear
python lookup.py supplier_name ΜΕΤΡΟ

# List every account code under a category
python lookup.py accounts 62.07

# Search accounts by Greek keyword (branch name, type of expense, etc.)
python lookup.py find_account ΚΕΡΚΥΡΑ
python lookup.py find_account ΚΑΥΣΙΜΑ

# Get the best-matching account for a category + branch + VAT rate
python lookup.py best_account 62.07 ΚΕΡΚΥΡΑ 24
python lookup.py best_account 64.00 ΑΔΑΜΑΝΤΑΣ 24

# Look up a specific account code
python lookup.py account 62.07.33724
```

---

## Source Files (do not modify)

| File | Contents |
|------|----------|
| `../excel/1. ΛΟΓΙΣΤΙΚΟ ΣΧΕΔΙΟ.xlsx` | Chart of accounts — 637 codes across 3 sheets |
| `../excel/4. ΠΑΡΑΔΕΙΓΜΑΤΑ ΕΓΓΡΑΦΩΝ.xlsx` | 5 example journal entries (ground truth) |
| `../excel/6β. ΑΡΧΕΙΟ ΠΡΟΜΗΘΕΥΤΩΝ.xlsx` | 6,322 supplier records with codes and ΑΦΜ |
| `../pdfs/named/` | 14 labeled PDFs (invoices by document type) |
| `../pdfs/sdoc/` | 21 raw scan PDFs (SDOC series) |
| `../_images/` | All PDFs rendered as PNG images (for reading scanned documents) |

To regenerate `data/` from the Excel files after any update:
```bash
python build_indexes.py
```

---

## Quick Reference

| Document type | Key accounts | Notes |
|---------------|-------------|-------|
| Fuel invoice | DR 64.00.xxxxx + DR 54.00.64024 / CR 50.xx | Branch in account code |
| Vehicle repair | DR 62.07.3xxxx + DR 54.00.62024 / CR 50.xx | 30xxx = vehicle |
| Building repair | DR 62.07.1xxxx + DR 54.00.62024 / CR 50.xx | 10xxx = building |
| Leasing (Eurobank) | DR 61.98.00824 + DR 54.00.62024 / CR 50.xx | |
| Rent payment | DR 62.04.000xx / CR 38.03.00009 | Per-landlord code |
| Road tax | DR 63.03.00000 / CR 38.03.00009 | No VAT |
| Transfer tax | DR 63.98.00101 / CR 38.03.00009 | No VAT |
| Port fines | DR 63.04.001xx / CR 38.03.00009 | By municipality |
| METRO (food) | DR 60.02.xxxxx + DR 63.98.00813/824 | VAT non-deductible! |
| METRO (cleaning) | DR 64.08.xxxxx + DR 54.00.64024 | VAT deductible |
| Electricity (ΔΕΗ) | DR 62.98.1xxxx + DR 54.00.62006 | Mixed 0%/6% |
| Telecom (OTE) | DR 62.03.00xxx + DR 54.00.62024 | Per-branch |
| Viva/card fees | DR 65.98.00900 / CR 38.03.00009 | |

**Primary bank account:** `38.03.00009` — ΠΕΙΡΑΙΩΣ ΟΨΕΩΣ
