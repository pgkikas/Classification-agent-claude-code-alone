# CLASSIFICATION RULEBOOK
## ΠΡΟΠΟΡΕΙΑ Α.Ε. (Avance Rent A Car) | ΑΦΜ: 095600200

---

## CRITICAL INSIGHT: How Account Codes Actually Work

The 5-digit suffix is **NOT a derivable formula**. It is an opaque lookup key.
The last 2 digits suggest VAT rate ONLY in some subgroups (62.07 vehicle, 64.00 fuel).
In others (62.04 rents, 62.05 insurance, 63.xx taxes, 38.xx banks) the suffix is a
sequential/historical ID with no formula.

**Rule: Always look up. Never guess a code.**

### Available Tools
```
python lookup.py accounts <subgroup>              # list all codes under e.g. 62.07
python lookup.py find_account <greek-keyword>     # search by description word
python lookup.py best_account <subgroup> <branch> <vat>  # scored match
python lookup.py supplier <AFM>                   # look up supplier by tax ID
python lookup.py supplier_name <name-word>        # search supplier by name
```

---

## ACCOUNT STRUCTURE — TRUE TAXONOMY

### Group 60 — Personnel
| Subgroup | Type | Notes |
|----------|------|-------|
| 60.00 | Salaries | 60.00.00000 |
| 60.02 | Canteen / work clothing | Per-branch (60.02.xxxxx where suffix encodes branch) |
| 60.03 / 60.04 | Employer contributions | 60.03.00000 |

### Group 61 — Third-party Fees (Αμοιβές Τρίτων)
| Subgroup | Type | Notes |
|----------|------|-------|
| 61.00 | Legal / professional fees | Sequential IDs (00010=lawyers no VAT, 00024=lawyers with VAT) |
| 61.02 | Sales commissions | |
| 61.98 | Leasing installments | 00620=ΕΤΕ Leasing, 00624=ΕΤΕ 24%, 00720=Πειραιώς, 00820=Eurobank ΑΝΕΥ, 00824=Eurobank 24% |

### Group 62 — Third-party Services (Παροχές Τρίτων)
| Subgroup | Type | Notes |
|----------|------|-------|
| 62.03 | Telecom | Pattern: 00BBB24 where BBB is sequential branch (000=KEN, 001=AGGEL, 002=MAR, etc.) |
| 62.04 | Rents | Each entry is a specific landlord/property — fully sequential |
| 62.05 | Insurance | Sequential by policy type |
| **62.07** | **Repairs & Maintenance** | **3 sub-types: 10xxx=BUILDING, 30xxx=VEHICLE, 40xxx=EQUIPMENT** |
| 62.98 | Utilities (elec/water) | Electricity: 10xxx, 11xxx, 12xxx... by location; Water: 000xx |

### 62.07 Sub-type Detail:
```
10xxx = Building/premises repairs (κτίρια)
  - 10000/10024 = ΚΕΝΤΡΙΚΟ (ΣΥΓΓΡΟΥ 40-42)
  - 10200/10224 = ΜΑΡΟΥΣΙ
  - 11024 = ΜΕΣΑΡΙΑ
  ...
30xxx = Vehicle maintenance (ΜΕΤ.ΜΕΣΑ) ← most common for Avance
  - 30000/30024 = ΚΕΝΤΡΙΚΟ
  - 30124 = ΑΓΓΕΛΑΚΗ
  - 30224 = ΜΑΡΟΥΣΙ
  - 30324 = ΣΑΝΤΟΡΙΝΗ
  - 30424 = ΜΥΚΟΝΟΣ
  - 30724 = ΗΛΙΟΥΠΟΛΗ
  - 31024 = ΜΕΣΑΡΙΑ
  - 31324 = ΛΥΚΟΥΡΓΟΥ (ΚΑΛΑΜΑΤΑ)
  - 31824 = ΠΕΡΑΙΑ
  - 32024 = ΣΚΑΛΑΔΟ
  - 32224 = ΕΛ.ΒΕΝΙΖΕΛΟΣ
  - 33024 = ΑΔΑΜΑΝΤΑΣ ΜΗΛΟΥ
  - 33124 = ΑΕΡ.ΜΗΛΟΥ
  - 33224 = ΤΗΝΟΣ
  - 33424 = ΗΡΑΚΛΕΙΟ ΚΡΗΤΗΣ
  - 33724 = ΚΕΡΚΥΡΑ
40xxx = Equipment/other maintenance
  - 40024 = ΚΕΝΤΡΙΚΟ
  - 41024 = ΜΕΣΑΡΙΑ
  ...
```

### Group 63 — Taxes & Duties
| Subgroup | Type | Notes |
|----------|------|-------|
| 63.03 | Road tax | 63.03.00000 (one code, no branch) |
| 63.04 | Municipal port duties 0.5% | Sequential by municipality: 00100=ΜΥΚΟΝΟΣ, 00101=ΣΑΝΤΟΡΙΝΗ, 00102=ΑΘΗΝΑ, 00103=ΜΗΛΟΣ, 00104=ΤΗΝΟΣ, 00105=ΗΡ.ΚΡΗΤΗΣ, 00106=ΚΕΡΚΥΡΑ, 00107=ΘΕΣΣ/ΝΙΚΗ |
| 63.98 | Misc taxes & stamp duties | Sequential: 00000=stamp on rents, 00101=transfer fees/plates, 00813=non-ded.VAT 13%, 00824=non-ded.VAT 24% |

### Group 64 — Operating Expenses
| Subgroup | Type | Notes |
|----------|------|-------|
| **64.00** | **Fuel & transport** | Branch-coded fuel accounts: 00024=KEN, 37024=ΚΕΡΚΥΡΑ, 23024=ΑΔΑΜΑΝΤΑΣ... Use lookup! |
| 64.01 | Travel expenses | |
| 64.02 | Advertising | |
| 64.05 | Subscriptions | |
| 64.07 | Stationery / IT consumables | |
| 64.08 | Cleaning materials | 00006/024=KEN 6%/24%, 01006/024=ΘΕΣΣ 6%/24%, 37006/024=ΚΕΡΚΥΡΑ |
| 64.98 | Misc expenses | Per-branch: 00024=KEN, 00100=ΑΓΓΕΛΑΚΗ, 00200=ΜΑΡΟΥΣΙ, 37013=ΚΕΡΚΥΡΑ |

### Group 65 — Financial Expenses
| Subgroup | Type | Notes |
|----------|------|-------|
| 65.01 | Loan interest | By bank: 00002=Eurobank, 00003=Πειραιώς |
| 65.98 | Banking fees / card fees | 00099=misc bank, 00700=AmEx, 00800=PayPal, 00900=VIVA, 01000=Euronet, 01100=Nexi/Alpha, 01200=Worldline/Eurobank |

### VAT Accounts (54.00)
| Code | Description |
|------|-------------|
| 54.00.62006 | VAT on 62.xx services @6% |
| 54.00.62013 | VAT on 62.xx services @13% |
| 54.00.62024 | VAT on 62.xx services @24% |
| 54.00.61024 | VAT on 61.xx fees @24% |
| 54.00.64006 | VAT on 64.xx expenses @6% |
| 54.00.64013 | VAT on 64.xx expenses @13% |
| 54.00.64024 | VAT on 64.xx expenses @24% |
| 63.98.00813 | Non-deductible VAT @13% (food/canteen) |
| 63.98.00824 | Non-deductible VAT @24% (food/canteen) |

**VAT routing rule:**
- 62.xx expense → VAT to 54.00.62{rate}
- 61.xx expense → VAT to 54.00.61{rate}
- 64.xx expense → VAT to 54.00.64{rate}
- Food/canteen (60.02) → VAT to 63.98.008{rate} (NON-DEDUCTIBLE — does NOT go to 54)
- State taxes / no-VAT → no VAT account

### Bank Accounts (38.03)
| Code | Bank |
|------|------|
| 38.03.00001 | EUROBANK ΟΨΕΩΣ |
| 38.03.00002 | ALPHA BANK ΟΨΕΩΣ |
| 38.03.00003 | ΕΘΝΙΚΗ ΤΡΑΠΕΖΑ |
| 38.03.00009 | ΠΕΙΡΑΙΩΣ ΟΨΕΩΣ 5052-026546-816 ← primary |

---

## CLASSIFICATION DECISION TREE

```
STEP 1: Identify document type
  (a) Invoice / ΤΠΥ / ΤΔΑ / Τιμολόγιο  → has supplier, amounts, VAT
  (b) Bank payment confirmation           → shows debit from 38.03.xx
  (c) Receipt / Απόδειξη                 → retail purchase, simplified
  (d) Bank statement line               → may need 2 entries (expense + bank)

STEP 2: Identify supplier
  → Search by AFM: python lookup.py supplier <AFM>
  → If not found by AFM: python lookup.py supplier_name <keyword>
  → Get supplier code: 50.00.xxxxx

STEP 3: Identify expense category
  Keywords → Subgroup:
  ΚΑΥΣΙΜ / ΠΕΤΡΕΛΑΙ / ΒΕΝΖΙΝ              → 64.00
  ΕΠΙΣΚΕΥ / ΣΥΝΤΗΡ / ΑΝΑΛΩΣΙΜ (vehicle)  → 62.07.3xxxx
  ΕΠΙΣΚΕΥ / ΣΥΝΤΗΡ (building/premises)    → 62.07.1xxxx
  ΜΙΣΘΩΜ / LEASING / ΧΡΗΜΑΤΟΔΟΤ          → 61.98.008xx
  ΕΝΟΙΚΙ                                  → 62.04.000xx
  ΤΗΛΕΦΩΝ / OTE / COSMOTE / WIND          → 62.03.00xxx
  ΔΕΗ / ΡΕΥΜΑ / ΦΩΤΙΣΜ                   → 62.98.1xxxx or 62.98.2xxxx
  ΥΔΡΕΥΣ / ΝΕΡΟ / ΕΥΔΑΠ / RAINBOW        → 62.98.000xx
  ΜΕΤΡΟ (food items)                      → 60.02.xxxxx (non-deduct VAT)
  ΜΕΤΡΟ (cleaning items)                  → 64.08.xxxxx
  ΤΕΛΗ ΚΥΚΛΟΦΟΡΙΑΣ                        → 63.03.00000
  ΤΕΛΟΣ ΜΕΤΑΒΙΒ / ΠΑΡΑΒΟΛΟ               → 63.98.00101
  ΚΛΗΣΕΙΣ / ΔΗΜΟΤΙΚ ΤΕΛΗ                 → 63.04.001xx
  ΑΣΦΑΛΙΣΤΡΑ                              → 62.05.000xx
  ΔΙΚΗΓΟΡ / ΝΟΜΙΚ / ΣΥΜΒΟΛΑΙΟΓΡ          → 61.00.000xx
  VIVA / NEXI / EURONET / WORLDLINE       → 65.98.009xx
  ΤΟΚΟΙ / ΤΡΑΠΕΖΙΚΑ ΕΞΟΔΑ               → 65.98 or 65.01
  ΕΙΔΗ ΕΝΔΥΣΕΩΣ / ΡΟΥΧΑ / ΣΤΟΛΗ         → 60.02.00024

STEP 4: Identify branch
  From: delivery address, invoice header location, vehicle plate context
  Common: ΚΕΝΤΡΙΚΟ (ΑΘΗΝΑ), ΑΓΓΕΛΑΚΗ (ΘΕΣ/ΝΙΚΗ), ΜΑΡΟΥΣΙ, ΣΑΝΤΟΡΙΝΗ,
          ΜΥΚΟΝΟΣ, ΑΔΑΜΑΝΤΑΣ (ΜΗΛΟΣ), ΤΗΝΟΣ, ΚΕΡΚΥΡΑ, ΗΡΑΚΛΕΙΟ, ΕΛ.ΒΕΝΙΖΕΛΟΣ

STEP 5: Find exact account code
  → python lookup.py best_account <subgroup> <branch> <vat_rate>
  → OR: python lookup.py find_account <branch_name>
  → VERIFY against description — do not assign blindly

STEP 6: Build journal entry
  For INVOICE:
    DR [expense account]        net amount
    DR [VAT account 54.00.xx]   VAT amount
    CR [supplier 50.00.xxxxx]   total gross

  For BANK PAYMENT (state/tax):
    DR [expense 63.xx]          amount
    CR [bank 38.03.00009]       amount

  For BANK PAYMENT (to supplier already invoiced):
    DR [supplier 50.00.xxxxx]   amount
    CR [bank 38.03.00009]       amount
```

---

## GROUND-TRUTH EXAMPLES (from `4.ΠΑΡΑΔΕΙΓΜΑΤΑ ΕΓΓΡΑΦΩΝ.xlsx`)

### E1: ICAR PRODUCTS — Vehicle cleaning supplies, ΚΕΡΚΥΡΑ
```
CR 50.00.05314  ICAR PRODUCTS            259.90
DR 62.07.33724  ΜΕΤ.ΜΕΣΑ ΚΕΡΚΥΡΑ 24%   209.60
DR 54.00.62024  ΦΠΑ ΠΑΡΟΧΩΝ 24%          50.30
```

### E2: ΞΥΔΟΥΣ — Fuel for ΧΒΑ3037, ΑΔΑΜΑΝΤΑΣ ΜΗΛΟΣ
```
CR 50.00.04200  ΞΥΔΟΥΣ Α.& ΣΙΑ Ε.Ε.     20.00
DR 64.00.23024  ΚΑΥΣΙΜΑ ΑΔΑΜΑΝΤ.ΜΗΛΟΣ   16.13
DR 54.00.64024  ΦΠΑ ΔΙΑΦ.ΕΞΟΔΩΝ 24%      3.87
```

### E3: ΑAΔΕ — Road tax, IYK9295
```
DR 63.03.00000  ΤΕΛΗ ΚΥΚΛΟΦΟΡΙΑΣ        27.68
CR 38.03.00009  ΠΕΙΡΑΙΩΣ ΟΨΕΩΣ          27.68
```

### E4a: ΠΕΡΙΦΕΡΕΙΑ ΑΤΤΙΚΗΣ — Transfer tax, XHA1725
```
DR 63.98.00101  ΕΞΟΔΑ ΕΚΔ.ΠΙΝΑΚΙΔΩΝ     75.00
CR 38.03.00009  ΠΕΙΡΑΙΩΣ ΟΨΕΩΣ          75.00
```
### E4b: ΠΕΙΡΑΙΩΣ — Bank fee on transfer
```
DR 50.00.03139  ΤΡΑΠΕΖΑ ΠΕΙΡΑΙΩΣ Α.Ε.    0.60
CR 38.03.00009  ΠΕΙΡΑΙΩΣ ΟΨΕΩΣ           0.60
```

### E5: ΜΕΤΡΟ — Mixed canteen + cleaning, ΚΕΝΤΡΙΚΟ (total 140.63 €)

The invoice VAT summary shows: 13%: 90.95 net | 24%: **28.24 net** | 6%: 2.68 net
⚠ The 24% row is COMBINED (food@24% = 7.24 + cleaning@24% = 21.00). Must split by item.

How to split: read each product line, categorise (food vs cleaning), then SUM per (category, rate):
- food@13%: coffee, milk, water, sugar, beverages            → net 90.95
- food@24%: non-stick paper, espresso base, shopping bags    → net  7.24
- cleaning@6%: shower gel / hygiene                          → net  2.68
- cleaning@24%: bakery paper rolls, clothespins, detergent   → net 21.00

**ONE single entry — confirmed from ground-truth Excel:**
```
CR 50.00.02732  ΜΕΤΡΟ Α.Ε.             140.63   ← single CR, full invoice total
DR 60.02.00000  ΚΥΛΙΚΕΙΟ ΚΕΝΤΡΙΚΟ       90.95   ← food net @13%
DR 63.98.00813  NON-DEDUCT VAT 13%      11.82   ← food VAT (non-deductible!)
DR 60.02.00000  ΚΥΛΙΚΕΙΟ ΚΕΝΤΡΙΚΟ        7.24   ← food net @24%
DR 63.98.00824  NON-DEDUCT VAT 24%       1.74   ← food VAT (non-deductible!)
DR 64.08.00006  ΥΛΙΚΑ ΚΑΘΑΡ. ΚΕΝΤΡ. 6%  2.68   ← cleaning @6%
DR 54.00.64006  ΦΠΑ ΔΙΑΦ.ΕΞΟΔΩΝ 6%      0.16   ← cleaning VAT (deductible)
DR 64.08.00024  ΥΛΙΚΑ ΚΑΘΑΡ. ΚΕΝΤΡ. 24% 21.00  ← cleaning @24%
DR 54.00.64024  ΦΠΑ ΔΙΑΦ.ΕΞΟΔΩΝ 24%     5.04   ← cleaning VAT (deductible)
```
Total DR = 140.63 = CR ✓
⚠ ONE entry, ONE CR line for the full supplier total — even when categories mix.

---

## IMPORTANT RULES / GOTCHAS

1. **One document can need 2+ journal entries** (e.g. bank transfer: tax + bank fee = 2 entries)
2. **METRO: food VAT → 63.98 (non-deductible), cleaning VAT → 54.00 (deductible)**
3. **Bank payment confirmations** are usually supporting documents FOR an existing invoice entry — check if you also have the invoice
4. **62.04 rent codes** are per-landlord, not per-branch formula — look up by landlord name
5. **Vehicle plate on invoice** → helps identify branch (e.g. IYK9295 is tracked to Κεντρικό fleet)
6. **Leasing (61.98)**: Eurobank=00820/00824, ΕΤΕ=00620/00624, Πειραιώς=00720/00724, Attica=00920/00924
7. **62.07 has 3 sub-types** — always check if the repair is for a VEHICLE (30xxx), BUILDING (10xxx), or EQUIPMENT (40xxx)
8. **Supplier codes 50.xx**: if not in archive, assign a new sequential code (max existing +1) or flag for accountant
