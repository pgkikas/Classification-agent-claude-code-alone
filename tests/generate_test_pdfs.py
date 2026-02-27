"""
SYNTHETIC TEST INVOICE GENERATOR
=================================
Generates 15 realistic Greek accounting invoices for testing the classification agent.
Each PDF is designed so the correct journal entry is derivable from RULEBOOK + lookup tools,
NOT from the agent's previous outputs.

Run:
    cd _workspace
    python tests/generate_test_pdfs.py

Output: tests/pdfs/TC1_*.pdf ... TC15_*.pdf
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                 Paragraph, Spacer, HRFlowable)
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT

# ── Font setup (Arial supports Greek Unicode) ─────────────────────────────────

FONT_PATH_REG  = "C:/Windows/Fonts/arial.ttf"
FONT_PATH_BOLD = "C:/Windows/Fonts/arialbd.ttf"

pdfmetrics.registerFont(TTFont("Arial",     FONT_PATH_REG))
pdfmetrics.registerFont(TTFont("Arial-Bold", FONT_PATH_BOLD))

OUT_DIR = os.path.join(os.path.dirname(__file__), "pdfs")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Style helpers ─────────────────────────────────────────────────────────────

def style(size=9, bold=False, align=TA_LEFT, color=colors.black):
    return ParagraphStyle(
        name="s",
        fontName="Arial-Bold" if bold else "Arial",
        fontSize=size,
        leading=size + 3,
        textColor=color,
        alignment=align,
    )

GREY  = colors.HexColor("#555555")
LGREY = colors.HexColor("#f4f4f4")
BLUE  = colors.HexColor("#1a3a6b")

# ── Core invoice builder ───────────────────────────────────────────────────────

def make_invoice(filename, doc_type_label, doc_no, doc_date,
                 seller, buyer, items, note=None):
    """
    seller / buyer: dicts with keys: name, afm, doy, addr
    items: list of dicts with: desc, qty, unit, unit_price, net, vat_pct, vat_amt, gross
    """
    path = os.path.join(OUT_DIR, filename)
    doc  = SimpleDocTemplate(path, pagesize=A4,
                             leftMargin=1.5*cm, rightMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []

    # ── Title bar ─────────────────────────────────────────────────────────────
    title_data = [[
        Paragraph(seller["name"], style(11, bold=True, color=BLUE)),
        Paragraph(f"<b>{doc_type_label}</b>", style(10, bold=True, align=TA_RIGHT, color=BLUE)),
    ]]
    t = Table(title_data, colWidths=[11*cm, 7*cm])
    t.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(t)
    story.append(HRFlowable(width="100%", thickness=2, color=BLUE, spaceAfter=6))

    # ── Seller / Doc info row ─────────────────────────────────────────────────
    def seller_lines():
        lines = [
            f"ΑΦΜ: <b>{seller['afm']}</b>",
            f"Δ.Ο.Υ.: {seller['doy']}",
            seller["addr"],
        ]
        if seller.get("phone"):
            lines.append(f"Τηλ.: {seller['phone']}")
        return "<br/>".join(lines)

    def doc_info():
        return (f"Αρ. Τιμολογίου: <b>{doc_no}</b><br/>"
                f"Ημερομηνία: <b>{doc_date}</b>")

    info_data = [[
        Paragraph(seller_lines(), style(8.5)),
        Paragraph(doc_info(), style(8.5, align=TA_RIGHT)),
    ]]
    t = Table(info_data, colWidths=[11*cm, 7*cm])
    t.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"),
                            ("TOPPADDING", (0,0), (-1,-1), 2)]))
    story.append(t)
    story.append(Spacer(1, 0.3*cm))

    # ── Buyer box ─────────────────────────────────────────────────────────────
    buyer_lines = (
        f"<b>Αγοραστής:</b> {buyer['name']}<br/>"
        f"ΑΦΜ: <b>{buyer['afm']}</b> &nbsp;&nbsp; Δ.Ο.Υ.: {buyer['doy']}<br/>"
        f"{buyer['addr']}"
    )
    buyer_t = Table([[Paragraph(buyer_lines, style(8.5))]],
                    colWidths=[18*cm])
    buyer_t.setStyle(TableStyle([
        ("BOX",           (0,0), (-1,-1), 0.5, GREY),
        ("BACKGROUND",    (0,0), (-1,-1), LGREY),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
    ]))
    story.append(buyer_t)

    if note:
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(f"<i>{note}</i>", style(8, color=GREY)))

    story.append(Spacer(1, 0.4*cm))

    # ── Items table ───────────────────────────────────────────────────────────
    col_w = [7.5*cm, 1.5*cm, 1.5*cm, 2*cm, 2*cm, 1.3*cm, 2.2*cm]
    header = ["Περιγραφή", "Ποσ.", "Μον.", "Τιμή Μον.", "Καθ. Αξία", "ΦΠΑ%", "Σύνολο"]
    rows = [[Paragraph(h, style(8, bold=True, align=TA_CENTER)) for h in header]]

    for it in items:
        rows.append([
            Paragraph(it["desc"], style(8)),
            Paragraph(str(it["qty"]),  style(8, align=TA_RIGHT)),
            Paragraph(it.get("unit","τεμ"), style(8, align=TA_CENTER)),
            Paragraph(f"{it['unit_price']:.2f}", style(8, align=TA_RIGHT)),
            Paragraph(f"{it['net']:.2f}",        style(8, align=TA_RIGHT)),
            Paragraph(str(it["vat_pct"]),         style(8, align=TA_CENTER)),
            Paragraph(f"{it['gross']:.2f}",       style(8, align=TA_RIGHT)),
        ])

    items_t = Table(rows, colWidths=col_w, repeatRows=1)
    items_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), BLUE),
        ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, LGREY]),
        ("BOX",           (0,0), (-1,-1), 0.5, GREY),
        ("INNERGRID",     (0,0), (-1,-1), 0.25, colors.lightgrey),
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("LEFTPADDING",   (0,0), (-1,-1), 4),
        ("RIGHTPADDING",  (0,0), (-1,-1), 4),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(items_t)
    story.append(Spacer(1, 0.4*cm))

    # ── VAT summary ───────────────────────────────────────────────────────────
    # Group by VAT rate (COMBINED across categories — this is the trap!)
    from collections import defaultdict
    vat_groups = defaultdict(lambda: {"net": 0.0, "vat": 0.0, "gross": 0.0})
    for it in items:
        g = vat_groups[it["vat_pct"]]
        g["net"]   += it["net"]
        g["vat"]   += it["vat_amt"]
        g["gross"] += it["gross"]

    total_gross = sum(it["gross"] for it in items)

    vat_header = ["Σύνολο ΦΠΑ", "Καθ. Αξία", "ΦΠΑ", "Σύνολο"]
    vat_rows = [[Paragraph(h, style(8, bold=True)) for h in vat_header]]
    for rate in sorted(vat_groups):
        g = vat_groups[rate]
        vat_rows.append([
            Paragraph(f"Συντελεστής {rate}%", style(8)),
            Paragraph(f"{g['net']:.2f}",   style(8, align=TA_RIGHT)),
            Paragraph(f"{g['vat']:.2f}",   style(8, align=TA_RIGHT)),
            Paragraph(f"{g['gross']:.2f}", style(8, align=TA_RIGHT)),
        ])

    vat_t = Table(vat_rows, colWidths=[5*cm, 3*cm, 3*cm, 3*cm])
    vat_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), colors.HexColor("#d0d8e8")),
        ("BOX",           (0,0), (-1,-1), 0.5, GREY),
        ("INNERGRID",     (0,0), (-1,-1), 0.25, colors.lightgrey),
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("LEFTPADDING",   (0,0), (-1,-1), 4),
        ("RIGHTPADDING",  (0,0), (-1,-1), 4),
    ]))

    total_t = Table(
        [[Paragraph("ΣΥΝΟΛΟ ΤΙΜΟΛΟΓΙΟΥ:", style(10, bold=True, align=TA_RIGHT)),
          Paragraph(f"{total_gross:.2f} €", style(10, bold=True, align=TA_RIGHT))]],
        colWidths=[12*cm, 6*cm]
    )
    total_t.setStyle(TableStyle([
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))

    summary_outer = Table([[vat_t, total_t]], colWidths=[14.5*cm, None])
    summary_outer.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "BOTTOM")]))
    story.append(summary_outer)

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.6*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GREY))
    story.append(Paragraph(
        "Το παρόν τιμολόγιο εκδόθηκε σύμφωνα με τις διατάξεις του Κ.Φ.Α.Σ.",
        style(7, color=GREY, align=TA_CENTER)
    ))

    doc.build(story)
    print(f"  OK {filename}")
    return path


# ── BUYER (always PROPORIA) ───────────────────────────────────────────────────

PROPORIA = dict(
    name="ΠΡΟΠΟΡΕΙΑ Α.Ε. (AVANCE RENT A CAR)",
    afm="095600200",
    doy="ΚΕΦΟΔΕ ΑΤΤΙΚΗΣ",
    addr="Λ. Βουλιαγμένης 318, Αγ. Δημήτριος 17343",
)

# ── TC1: FUEL RECEIPT — ΜΗΛΟΣ ────────────────────────────────────────────────
# Supplier: ΞΥΔΟΥΣ Α.& ΣΙΑ Ε.Ε.  |  AFM: 998455605  |  Code: 50.00.04200
# Branch:   ΑΔΑΜΑΝΤΑΣ ΜΗΛΟΣ
# Expected: DR 64.00.23024 / DR 54.00.64024 / CR 50.00.04200
# Gross: 70.56  Net: 56.90  VAT@24%: 13.66

def tc1():
    seller = dict(
        name="ΞΥΔΟΥΣ ΑΝΔΡΕΑΣ ΚΑΙ ΣΙΑ ΕΤΕΡΟΡΡΥΘΜΗ ΕΤΑΙΡΕΙΑ",
        afm="998455605",
        doy="ΦΑΕ ΠΕΙΡΑΙΑ",
        addr="Αδάμαντας Μήλου, 848 01 ΜΗΛΟΣ",
        phone="22870-22200",
    )
    buyer = dict(PROPORIA, addr="Αδάμαντας Μήλου — όχημα ΧΒΑ-3037")

    items = [
        dict(desc="Αμόλυβδη βενζίνη 95 (RON)",
             qty=42.00, unit="lt", unit_price=1.680,
             net=56.90, vat_pct=24, vat_amt=13.66, gross=70.56),
    ]
    make_invoice(
        "TC1_fuel_milos.pdf",
        "ΑΠΟΔΕΙΞΗ ΛΙΑΝΙΚΗΣ ΠΩΛΗΣΗΣ — ΚΑΥΣΙΜΑ",
        "Β-012847", "31/01/2026",
        seller, buyer, items,
        note="Σταθμός υγρών καυσίμων — Αδάμαντας Μήλου",
    )


# ── TC2: VEHICLE REPAIR — ΜΥΚΟΝΟΣ ────────────────────────────────────────────
# Supplier: ICAR PRODUCTS ΜΟΝΟΠΡΟΣΩΠΗ Ι.Κ.Ε.  |  AFM: 802204319  |  Code: 50.00.05314
# Branch:   ΜΥΚΟΝΟΣ (Α/Δ ΜΥΚΟΝΟΥ)
# Expected: DR 62.07.30424 / DR 54.00.62024 / CR 50.00.05314
# Gross: 105.00  Net: 84.68  VAT@24%: 20.32

def tc2():
    seller = dict(
        name="ICAR PRODUCTS ΜΟΝΟΠΡΟΣΩΠΗ Ι.Κ.Ε.",
        afm="802204319",
        doy="Αχαρνών",
        addr="Λεωφ. Μεγάλου Αλεξάνδρου 128, Άνω Λιόσια",
        phone="210-2481234",
    )
    buyer = dict(PROPORIA)

    items = [
        dict(desc="Αλλαγή λαδιών κινητήρα — Shell Helix 5W40 5L",
             qty=1, unit="τεμ", unit_price=85.00,
             net=68.55, vat_pct=24, vat_amt=16.45, gross=85.00),
        dict(desc="Φίλτρο λαδιού OEM (Mann W712/93)",
             qty=1, unit="τεμ", unit_price=12.00,
             net=9.68, vat_pct=24, vat_amt=2.32, gross=12.00),
        dict(desc="Αντιπαγωτικό υαλοκαθαριστήρα −20°C, 1L",
             qty=1, unit="τεμ", unit_price=8.00,
             net=6.45, vat_pct=24, vat_amt=1.55, gross=8.00),
    ]
    make_invoice(
        "TC2_repair_mykonos.pdf",
        "ΤΙΜΟΛΟΓΙΟ ΠΑΡΟΧΗΣ ΥΠΗΡΕΣΙΩΝ",
        "Τ-006423", "15/01/2026",
        seller, buyer, items,
        note="Τόπος εκτέλεσης εργασιών: Αεροδρόμιο Μυκόνου — Avance Rent A Car",
    )


# ── TC3: TELECOM INVOICE — ΜΑΡΟΥΣΙ ───────────────────────────────────────────
# Supplier: NOVA ΤΗΛΕΠΙΚΟΙΝΩΝΙΕΣ ΜΟΝΟΠΡΟΣΩΠΗ ΑΕ  |  AFM: 094444827  |  Code: 50.00.00213
# Branch:   ΜΑΡΟΥΣΙ
# Expected: DR 62.03.00224 / DR 54.00.62024 / CR 50.00.00213
# Gross: 54.00  Net: 43.55  VAT@24%: 10.45

def tc3():
    seller = dict(
        name="NOVA ΤΗΛΕΠΙΚΟΙΝΩΝΙΕΣ ΜΟΝΟΠΡΟΣΩΠΗ ΑΕ",
        afm="094444827",
        doy="ΦΑΕ ΑΘΗΝΩΝ",
        addr="Λ. Κηφισίας 44, 151 25 Μαρούσι",
        phone="13831",
    )
    buyer = dict(PROPORIA, addr="Λ. Κηφισίας 100, 151 25 Μαρούσι — ΥΠΟΚ/ΜΑ ΑΜΑΡΟΥΣΙΟΥ")

    items = [
        dict(desc="Μηνιαία συνδρομή broadband internet (Φεβρουάριος 2026)",
             qty=1, unit="μήνας", unit_price=34.00,
             net=27.42, vat_pct=24, vat_amt=6.58, gross=34.00),
        dict(desc="Σταθερή τηλεφωνία — Πάγια + κλήσεις (Φεβρουάριος 2026)",
             qty=1, unit="μήνας", unit_price=20.00,
             net=16.13, vat_pct=24, vat_amt=3.87, gross=20.00),
    ]
    make_invoice(
        "TC3_telecom_maroussi.pdf",
        "ΤΙΜΟΛΟΓΙΟ ΠΑΡΟΧΗΣ ΥΠΗΡΕΣΙΩΝ",
        "ΤΠΥ-0048291", "05/02/2026",
        seller, buyer, items,
    )


# ── TC4: METRO FOOD-ONLY — ΚΕΝΤΡΙΚΟ ──────────────────────────────────────────
# Supplier: ΜΕΤΡΟ Α.Ε.  |  AFM: 094062259  |  Code: 50.00.02732
# Branch:   ΚΕΝΤΡΙΚΟ
# Items: all food/canteen, TWO different VAT rates (13% and 24%)
# ⚠ Tests non-deductible VAT path (63.98) and two DR lines for same account
# Expected:
#   DR 60.02.00000 @13%  15.25  /  DR 63.98.00813  1.98
#   DR 60.02.00000 @24%   9.19  /  DR 63.98.00824  2.21
#   CR 50.00.02732  28.63

def tc4():
    seller = dict(
        name="ΜΕΤΡΟ ΑΕΒΕ",
        afm="094062259",
        doy="ΦΑΕ ΑΘΗΝΩΝ",
        addr="Σπ. Πάτση 6 & Αγ. Αναργύρων, 121 31 Αθήνα",
        phone="210-5198000",
    )
    buyer = dict(PROPORIA, addr="Λ. Συγγρού 40-42, 117 42 Αθήνα — ΚΕΝΤΡΙΚΑ ΓΡΑΦΕΙΑ")

    items = [
        dict(desc="ΓΑΛΑ ΦΡΕΣΚΟ 1,5% ΠΑΠΑΔΟΠΟΥΛΟΣ 1L",
             qty=3, unit="τεμ", unit_price=1.31,
             net=3.93, vat_pct=13, vat_amt=0.51, gross=4.44),
        dict(desc="ΝΕΣΚΑΦΕ CLASSIC 200γρ",
             qty=2, unit="τεμ", unit_price=2.82,
             net=5.64, vat_pct=24, vat_amt=1.36, gross=7.00),
        dict(desc="ΧΥΜΟΣ ΠΟΡΤΟΚΑΛΙ AMITA 1L",
             qty=4, unit="τεμ", unit_price=1.49,
             net=5.96, vat_pct=13, vat_amt=0.77, gross=6.73),
        dict(desc="ΖΑΧΑΡΗ ΛΕΥΚΗ HELLAS SUGAR 1KG",
             qty=2, unit="τεμ", unit_price=0.80,
             net=1.60, vat_pct=13, vat_amt=0.21, gross=1.81),
        dict(desc="ΧΑΡΤΟΠΕΤΣΕΤΕΣ ZESTA 250 τεμ",
             qty=3, unit="τεμ", unit_price=1.18,
             net=3.55, vat_pct=24, vat_amt=0.85, gross=4.40),
        dict(desc="ΑΘΗΝΑΪΚΟ ΝΕΡΟ 1,5L",
             qty=6, unit="τεμ", unit_price=0.63,
             net=3.76, vat_pct=13, vat_amt=0.49, gross=4.25),
    ]
    make_invoice(
        "TC4_metro_food_only.pdf",
        "ΤΙΜΟΛΟΓΙΟ ΑΓΟΡΑΣ",
        "ΤΤ-0024156", "28/01/2026",
        seller, buyer, items,
        note="Αγορά ειδών κυλικείου — Κατάστημα ΜΕΤΡΟ Αθηνών (ΚΕΝΤΡΙΚΟ)",
    )


# ── TC5: METRO MIXED FOOD + CLEANING — ΚΕΝΤΡΙΚΟ ──────────────────────────────
# Supplier: ΜΕΤΡΟ Α.Ε.  |  AFM: 094062259  |  Code: 50.00.02732
# Branch:   ΚΕΝΤΡΙΚΟ
# ⚠ HARD CASE: items INTERLEAVED (food & cleaning mixed), 3 VAT rates
# ⚠ VAT summary 24% row is COMBINED (food@24% 8.87 + cleaning@24% 9.52 = 18.39)
# Expected:
#   Entry 1 — Τρόφιμα:
#     DR 60.02.00000 @13%  19.10  /  DR 63.98.00813   2.47
#     DR 60.02.00000 @24%   8.87  /  DR 63.98.00824   2.13
#     CR 50.00.02732  32.57
#   Entry 2 — Καθαριότητα:
#     DR 64.08.00006 @6%    3.77  /  DR 54.00.64006   0.23
#     DR 64.08.00024 @24%   9.52  /  DR 54.00.64024   2.28
#     CR 50.00.02732  15.80

def tc5():
    seller = dict(
        name="ΜΕΤΡΟ ΑΕΒΕ",
        afm="094062259",
        doy="ΦΑΕ ΑΘΗΝΩΝ",
        addr="Σπ. Πάτση 6 & Αγ. Αναργύρων, 121 31 Αθήνα",
        phone="210-5198000",
    )
    buyer = dict(PROPORIA, addr="Λ. Συγγρού 40-42, 117 42 Αθήνα — ΚΕΝΤΡΙΚΑ ΓΡΑΦΕΙΑ")

    # Interleaved: food and cleaning items are NOT grouped together
    items = [
        # food @13%
        dict(desc="JACOBS KRONUNG ΚΑΦΕΣ ΦΙΛΤΡΟΥ 500γρ",
             qty=2, unit="τεμ", unit_price=4.87,
             net=9.73, vat_pct=13, vat_amt=1.26, gross=10.99),
        # food @13%
        dict(desc="ΓΑΛΑ ΠΛΑΚΑ EΛΑΦΡΥ ΔΕΛΤΑ 1L",
             qty=4, unit="τεμ", unit_price=0.89,
             net=3.54, vat_pct=13, vat_amt=0.46, gross=4.00),
        # cleaning @6%
        dict(desc="FAIRY ORIGINAL DISHES 500ml",
             qty=1, unit="τεμ", unit_price=3.77,
             net=3.77, vat_pct=6, vat_amt=0.23, gross=4.00),
        # food @13%
        dict(desc="ΝΕΡΟ ΖΑΓΟΡΙ 1,5L",
             qty=6, unit="τεμ", unit_price=0.53,
             net=3.18, vat_pct=13, vat_amt=0.41, gross=3.59),
        # food @24%
        dict(desc="ΘΗΚΗ ΚΑΦΕ ΕΣΠΡΕΣΣΟ 100 τεμ",
             qty=1, unit="τεμ", unit_price=4.84,
             net=4.84, vat_pct=24, vat_amt=1.16, gross=6.00),
        # cleaning @24%
        dict(desc="BLANCOLOR ΧΛΩΡΙΝΗ 2L",
             qty=2, unit="τεμ", unit_price=1.94,
             net=3.87, vat_pct=24, vat_amt=0.93, gross=4.80),
        # food @13%
        dict(desc="ΖΑΧΑΡΗ ΦΑΚΕΛΑΚΙΑ DIAMANT 100x3γρ",
             qty=1, unit="τεμ", unit_price=2.65,
             net=2.65, vat_pct=13, vat_amt=0.34, gross=2.99),
        # food @24%
        dict(desc="ΧΑΡΤΙΝΕΣ ΣΑΚΟΥΛΕΣ ΤΡΟΦ. 20τεμ",
             qty=1, unit="τεμ", unit_price=4.03,
             net=4.03, vat_pct=24, vat_amt=0.97, gross=5.00),
        # cleaning @24%
        dict(desc="ARIEL ΑΠΟΡΡΥΠΑΝΤΙΚΟ ΣΚΟΝΗ 3KG",
             qty=1, unit="τεμ", unit_price=5.65,
             net=5.65, vat_pct=24, vat_amt=1.35, gross=7.00),
    ]
    make_invoice(
        "TC5_metro_mixed.pdf",
        "ΤΙΜΟΛΟΓΙΟ ΑΓΟΡΑΣ",
        "ΤΤ-0024392", "28/01/2026",
        seller, buyer, items,
        note="Αγορά ειδών κυλικείου & καθαριότητας — Κατάστημα ΜΕΤΡΟ Αθηνών (ΚΕΝΤΡΙΚΟ)",
    )


# ── Main ──────────────────────────────────────────────────────────────────────

# ── Bank confirmation template ────────────────────────────────────────────────

def make_bank_confirmation(filename, doc_date, from_account, to_payee,
                           amount, reference, amount_words=""):
    """Simple bank transfer confirmation — no supplier, no items."""
    path = os.path.join(OUT_DIR, filename)
    doc  = SimpleDocTemplate(path, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2*cm)
    story = []

    story.append(Paragraph("ΤΡΑΠΕΖΑ ΠΕΙΡΑΙΩΣ Α.Ε.", style(13, bold=True, color=BLUE)))
    story.append(Paragraph("Επιβεβαίωση Εντολής Πληρωμής / Payment Confirmation",
                            style(9, color=GREY)))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=BLUE, spaceAfter=8))

    rows = [
        ["Ημερομηνία:", doc_date],
        ["Λογαριασμός χρέωσης:", from_account],
        ["Δικαιούχος / Αποδέκτης:", to_payee],
        ["Αιτιολογία:", reference],
        ["Ποσό:", f"{amount:.2f} EUR"],
    ]
    if amount_words:
        rows.append(["Ποσό ολογράφως:", amount_words])
    rows.append(["Κατάσταση:", "ΕΚΤΕΛΕΣΘΗΚΕ"])

    t = Table(rows, colWidths=[5.5*cm, 12*cm])
    t.setStyle(TableStyle([
        ("FONTNAME",      (0,0), (0,-1), "Arial-Bold"),
        ("FONTNAME",      (1,0), (1,-1), "Arial"),
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.white, LGREY]),
        ("TEXTCOLOR",     (0,-1), (-1,-1), colors.HexColor("#1a7a1a")),
        ("FONTNAME",      (0,-1), (-1,-1), "Arial-Bold"),
    ]))
    story.append(t)
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(
        "Το παρόν αποτελεί επίσημο αποδεικτικό εκτέλεσης πληρωμής.",
        style(7.5, color=GREY, align=TA_CENTER)))
    story.append(Paragraph(
        f"GR74 0172 0520 0050 5202 6546 816  |  Ημ/νία εκτύπωσης: {doc_date}",
        style(7, color=GREY, align=TA_CENTER)))

    doc.build(story)
    print(f"  OK {filename}")
    return path


# ── TC6: ELECTRICITY — ΔΕΗ, ΚΕΝΤΡΙΚΟ ────────────────────────────────────────
# Supplier: ΔΕΗ ΑΕ | AFM: 090000045 | Code: 50.00.02296
# Account:  62.98.10006 ΦΩΤΙΣΜΟΣ ΚΕΝΤΡΙΚΟΥ 6%
# Gross: 150.00  Net: 141.51  VAT@6%: 8.49

def tc6():
    seller = dict(
        name="ΔΗΜΟΣΙΑ ΕΠΙΧΕΙΡΗΣΗ ΗΛΕΚΤΡΙΣΜΟΥ ΑΝΩΝΥΜΗ ΕΤΑΙΡΙΑ",
        afm="090000045",
        doy="ΦΑΕ ΑΘΗΝΩΝ",
        addr="Χαλκοκονδύλη 30, 104 32 Αθήνα",
        phone="11770",
    )
    buyer = dict(PROPORIA, addr="Λ. Βουλιαγμένης 318, 173 43 Αγ. Δημήτριος — ΚΕΝΤΡΙΚΟ")
    items = [
        dict(desc="Κατανάλωση ηλεκτρικής ενέργειας — 920 kWh (Χαμηλή τάση)",
             qty=920, unit="kWh", unit_price=0.1000,
             net=92.00, vat_pct=6, vat_amt=5.52, gross=97.52),
        dict(desc="Πάγια χρέωση & δικτυακές υπηρεσίες (Ιανουάριος 2026)",
             qty=1, unit="μήνας", unit_price=49.51,
             net=49.51, vat_pct=6, vat_amt=2.97, gross=52.48),
    ]
    make_invoice(
        "TC6_electricity_kentpiko.pdf",
        "ΕΚΚΑΘΑΡΙΣΗ ΗΛΕΚΤΡΙΚΗΣ ΕΝΕΡΓΕΙΑΣ",
        "ΔΕΗ-20260131-004827", "31/01/2026",
        seller, buyer, items,
        note="Παροχή No: 22345678 — Λ. Βουλιαγμένης 318, Αγ. Δημήτριος",
    )


# ── TC7: WATER — RAINBOW, ΚΕΝΤΡΙΚΟ ───────────────────────────────────────────
# Supplier: RAINBOW GROUP ΑΕ | AFM: 999808277 | Code: 50.00.01010
# Account:  62.98.00013 ΥΔΡΕΥΣΗ ΚΕΝΤΡΙΚΟΥ 13%
# Gross: 50.00  Net: 44.25  VAT@13%: 5.75

def tc7():
    seller = dict(
        name="RAINBOW GROUP ΑΝΩΝΥΜΗ ΕΤΑΙΡΕΙΑ ΕΜΦΙΑΛΩΜΕΝΟΥ ΝΕΡΟΥ",
        afm="999808277",
        doy="ΦΑΕ ΙΩΑΝΝΙΝΩΝ",
        addr="Λεωφ. Γράμμου 56, Ιωάννινα",
        phone="26510-29800",
    )
    buyer = dict(PROPORIA, addr="Λ. Βουλιαγμένης 318, 173 43 Αγ. Δημήτριος")
    items = [
        dict(desc="Εμφιαλωμένο νερό 19L — 2 φιάλες",
             qty=2, unit="τεμ", unit_price=17.70,
             net=35.40, vat_pct=13, vat_amt=4.60, gross=40.00),
        dict(desc="Μηνιαία μίσθωση ψύκτη νερού (Φεβρουάριος 2026)",
             qty=1, unit="μήνας", unit_price=8.85,
             net=8.85, vat_pct=13, vat_amt=1.15, gross=10.00),
    ]
    make_invoice(
        "TC7_water_kentpiko.pdf",
        "ΤΙΜΟΛΟΓΙΟ ΠΑΡΟΧΗΣ ΥΠΗΡΕΣΙΩΝ",
        "ΤΠΥ-2026-00841", "01/02/2026",
        seller, buyer, items,
    )


# ── TC8: FUEL — CORAL, ΚΕΡΚΥΡΑ ───────────────────────────────────────────────
# Supplier: CORAL ΑΕ | AFM: 094472979 | Code: 50.00.01837
# Account:  64.00.37024 ΕΞΟΔΑ ΚΙΝΗΣΗΣ-ΚΑΥΣΙΜΑ ΚΕΡΚΥΡΑ 24%
# Gross: 162.60  Net: 131.13  VAT@24%: 31.47
# (Multi-vehicle fuel card invoice)

def tc8():
    seller = dict(
        name="CORAL ΑΝΩΝΥΜΟΣ ΕΤΑΙΡΙΑ ΠΕΤΡΕΛΑΙΟΕΙΔΩΝ ΚΑΙ ΧΗΜΙΚΩΝ ΠΡΟΙΟΝΤΩΝ",
        afm="094472979",
        doy="ΦΑΕ ΑΘΗΝΩΝ",
        addr="Ηρώδου Αττικού 12, 151 24 Μαρούσι",
        phone="210-8097700",
    )
    buyer = dict(PROPORIA, addr="Αερολιμένας Κέρκυρας — ΥΠΟΚ/ΜΑ ΚΕΡΚΥΡΑΣ")
    items = [
        dict(desc="Αμόλυβδη βενζίνη 95 — ΚΙΟ-3124 (45,00 L @ 1,680)",
             qty=45.00, unit="lt", unit_price=1.680,
             net=60.97, vat_pct=24, vat_amt=14.63, gross=75.60),
        dict(desc="Diesel αυτοκινήτου — ΚΥΚ-5511 (60,00 L @ 1,450)",
             qty=60.00, unit="lt", unit_price=1.450,
             net=70.16, vat_pct=24, vat_amt=16.84, gross=87.00),
    ]
    make_invoice(
        "TC8_fuel_kerkyra.pdf",
        "ΤΙΜΟΛΟΓΙΟ ΠΩΛΗΣΗΣ — ΚΑΡΤΑ ΚΑΥΣΙΜΩΝ",
        "ΤΠ-20260131-CRF-00441", "31/01/2026",
        seller, buyer, items,
        note="Κάρτα καυσίμων: AVANCE RENT A CAR — Κέρκυρα",
    )


# ── TC9: VEHICLE REPAIR — ΜΕΙΔΑΝΗΣ, ΚΕΝΤΡΙΚΟ ────────────────────────────────
# Supplier: Α ΜΕΙΔΑΝΗΣ ΑΝΩΝΥΜΗ ΑΕ | AFM: 094356237 | Code: 50.00.01689
# Account:  62.07.30024 ΕΠΙΣΚ.ΜΕΤ.ΜΕΣΩΝ ΚΕΝΤΡΙΚΟΥ 24%
# Gross: 420.00  Net: 338.71  VAT@24%: 81.29

def tc9():
    seller = dict(
        name="Α. ΜΕΙΔΑΝΗΣ Η ΣΟΦΟΣ ΑΝΩΝΥΜΗ ΕΤΑΙΡΙΑ ΕΛΑΣΤΙΚΩΝ & ΟΡΥΚΤΕΛΑΙΩΝ",
        afm="094356237",
        doy="ΦΑΕ ΑΘΗΝΩΝ",
        addr="Ιφιγ. Δημητρ. Καλλικλ. 4, Αθήνα",
        phone="210-9821000",
    )
    buyer = dict(PROPORIA)
    items = [
        dict(desc="Ελαστικά Pirelli Cinturato P7 225/55R17 97W (x4)",
             qty=4, unit="τεμ", unit_price=90.08,
             net=360.32, vat_pct=24, vat_amt=86.48, gross=446.80),
        dict(desc="Εργασία τοποθέτησης & ζυγοστάθμιση (x4)",
             qty=4, unit="τεμ", unit_price=5.00,
             net=20.00, vat_pct=24, vat_amt=4.80, gross=24.80),
        dict(desc="Ευθυγράμμιση τετράτροχη",
             qty=1, unit="τεμ", unit_price=40.00,
             net=40.00, vat_pct=24, vat_amt=9.60, gross=49.60),
    ]
    make_invoice(
        "TC9_repair_kentpiko.pdf",
        "ΤΙΜΟΛΟΓΙΟ ΠΑΡΟΧΗΣ ΥΠΗΡΕΣΙΩΝ",
        "Τ-20260118-2891", "18/01/2026",
        seller, buyer, items,
        note="Εργασίες σε όχημα YNE-4412 — παραδόθηκε στα γραφεία Βουλιαγμένης",
    )


# ── TC10: VEHICLE REPAIR — ΜΠΟΤΟΣ, ΚΕΡΚΥΡΑ ──────────────────────────────────
# Supplier: ΜΠΟΤΟΣ ΘΕΟΦΑΝΗΣ | AFM: 073870458 | Code: 50.00.05488
# Account:  62.07.33724 ΕΠΙΣΚ.ΜΕΤ.ΜΕΣΩΝ ΚΕΡΚΥΡΑΣ 24%
# Gross: 235.00  Net: 189.52  VAT@24%: 45.48

def tc10():
    seller = dict(
        name="ΜΠΟΤΟΣ ΘΕΟΦΑΝΗΣ ΝΙΚΟΛΑΟΣ",
        afm="073870458",
        doy="ΚΕΡΚΥΡΑΣ",
        addr="Πολυφήμου 47, 491 00 Κέρκυρα",
        phone="26610-44321",
    )
    buyer = dict(PROPORIA, addr="Αεροδρόμιο Κέρκυρας Ι. Καποδίστριας — ΥΠΟΚ/ΜΑ ΚΕΡΚΥΡΑΣ")
    items = [
        dict(desc="Αντικατάσταση παρμπρίζ — Fuyao 62C FW (ΕΑΚ-7823)",
             qty=1, unit="τεμ", unit_price=220.00,
             net=177.42, vat_pct=24, vat_amt=42.58, gross=220.00),
        dict(desc="Υγρό υαλοκαθαριστήρων αντιπαγωτικό -20°C, 5L",
             qty=1, unit="τεμ", unit_price=15.00,
             net=12.10, vat_pct=24, vat_amt=2.90, gross=15.00),
    ]
    make_invoice(
        "TC10_repair_kerkyra.pdf",
        "ΤΙΜΟΛΟΓΙΟ ΠΑΡΟΧΗΣ ΥΠΗΡΕΣΙΩΝ",
        "ΤΠΥ-0003147", "22/01/2026",
        seller, buyer, items,
        note="Τόπος εκτέλεσης εργασιών: Αεροδρόμιο Κέρκυρας",
    )


# ── TC11: LEASING — EUROBANK, monthly installment ────────────────────────────
# Supplier: EUROBANK ΧΡΗΜΑΤΟΔΟΤΙΚΕΣ ΜΙΣΘΩΣΕΙΣ | AFM: 094324854 | Code: 50.00.03872
# Capital (no VAT): DR 61.98.00820 — 720.00
# Interest (VAT 24%): DR 61.98.00824 — 280.00 net / DR 54.00.61024 — 67.20
# CR 50.00.03872 — 1,067.20

def tc11():
    seller = dict(
        name="EUROBANK ERGASIAS ΧΡΗΜΑΤΟΔΟΤΙΚΕΣ ΜΙΣΘΩΣΕΙΣ ΜΟΝΟΠΡΟΣΩΠΗ ΑΕ",
        afm="094324854",
        doy="ΦΑΕ ΑΘΗΝΩΝ",
        addr="Εσλίν 7-13 & Αμαλιάδος 20, 115 23 Αθήνα",
        phone="210-3355000",
    )
    buyer = dict(PROPORIA)
    items = [
        # Capital portion — NO VAT (shown as 0%)
        dict(desc="Δόση κεφαλαίου Χρηματοδοτικής Μίσθωσης — Δόση No. 18/48",
             qty=1, unit="τεμ", unit_price=720.00,
             net=720.00, vat_pct=0, vat_amt=0.00, gross=720.00),
        # Interest portion — 24% VAT
        dict(desc="Χρεωστικοί τόκοι μίσθωσης (Φεβρουάριος 2026)",
             qty=1, unit="τεμ", unit_price=280.00,
             net=280.00, vat_pct=24, vat_amt=67.20, gross=347.20),
    ]
    make_invoice(
        "TC11_leasing_eurobank.pdf",
        "ΤΙΜΟΛΟΓΙΟ ΠΑΡΟΧΗΣ ΥΠΗΡΕΣΙΩΝ — LEASING",
        "ΤΠΥ-2026-EBL-001842", "01/02/2026",
        seller, buyer, items,
        note="Σύμβαση χρηματοδοτικής μίσθωσης No. EBL-20220418-4821",
    )


# ── TC12: INSURANCE — GENERALI, vehicle policy ───────────────────────────────
# Supplier: GENERALI HELLAS ΑΑΕ | AFM: 094327684 | Code: 50.00.02402
# Account:  62.05.00001 Ασφάλιστρα μεταφορικών μέσων — NO VAT on insurance
# Gross = Net: 385.00

def tc12():
    seller = dict(
        name="GENERALI HELLAS ΑΝΩΝΥΜΟΣ ΑΣΦΑΛΙΣΤΙΚΗ ΕΤΑΙΡΕΙΑ",
        afm="094327684",
        doy="ΦΑΕ ΑΘΗΝΩΝ",
        addr="Λεωφ. Συγγρού 97 & Λαγουμιτζή 40, 117 45 Αθήνα",
        phone="210-8095000",
    )
    buyer = dict(PROPORIA)
    items = [
        dict(desc="Ασφάλιστρα αστικής ευθύνης έναντι τρίτων — ΙΑΓ-2847 (01/02-31/07/2026)",
             qty=1, unit="τεμ", unit_price=285.00,
             net=285.00, vat_pct=0, vat_amt=0.00, gross=285.00),
        dict(desc="Ασφάλιστρα κλοπής — ΙΑΓ-2847",
             qty=1, unit="τεμ", unit_price=65.00,
             net=65.00, vat_pct=0, vat_amt=0.00, gross=65.00),
        dict(desc="Ασφάλιστρα πυρός & θύελλας — ΙΑΓ-2847",
             qty=1, unit="τεμ", unit_price=35.00,
             net=35.00, vat_pct=0, vat_amt=0.00, gross=35.00),
    ]
    make_invoice(
        "TC12_insurance_generali.pdf",
        "ΑΣΦΑΛΙΣΤΗΡΙΟ ΣΥΜΒΟΛΑΙΟ — ΤΙΜΟΛΟΓΙΟ",
        "ΑΣΦ-2026-00184291", "01/02/2026",
        seller, buyer, items,
        note="Πολιτικη No. GEN-AUTO-2026-4821 — ΙΑΓ-2847 — ΑΣΤΙΚΗ ΕΥΘΥΝΗ / ΚΛΟΠΗ / ΠΥΡ",
    )


# ── TC13: BANK PAYMENT — Road tax, ΑΑΔΕ ──────────────────────────────────────
# No supplier — payment to state
# DR 63.03.00000 / CR 38.03.00009
# Amount: 38.00

def tc13():
    make_bank_confirmation(
        "TC13_bank_roadtax.pdf",
        doc_date="15/01/2026",
        from_account="GR74 0172 0520 0050 5202 6546 816 — ΠΡΟΠΟΡΕΙΑ Α.Ε.",
        to_payee="ΑΑΔΕ — Τέλη Κυκλοφορίας (e-paravolo)",
        amount=38.00,
        reference="ΤΕΛΗ ΚΥΚΛΟΦΟΡΙΑΣ 2026 — ΑΡ. ΚΥΚΛΟΦΟΡΙΑΣ ΙΖΙ-1234 — e-paravolo: 2026012200001",
        amount_words="ΤΡΙΑΝΤΑ ΟΚΤΩ ΕΥΡΩ",
    )


# ── TC14: METRO CLEANING-ONLY — ΚΕΝΤΡΙΚΟ ─────────────────────────────────────
# Supplier: METRO ΑΕΒΕ | AFM: 094062259 | Code: 50.00.02732
# All cleaning items (64.08), two VAT rates: 6% and 24%
# No food — tests that agent uses 64.08 (deductible VAT → 54.00) not 60.02

def tc14():
    seller = dict(
        name="ΜΕΤΡΟ ΑΕΒΕ",
        afm="094062259",
        doy="ΦΑΕ ΑΘΗΝΩΝ",
        addr="Σπ. Πάτση 6 & Αγ. Αναργύρων, 121 31 Αθήνα",
        phone="210-5198000",
    )
    buyer = dict(PROPORIA, addr="Λ. Βουλιαγμένης 318, 173 43 Αγ. Δημήτριος — ΚΕΝΤΡΙΚΟ")
    items = [
        # @6%
        dict(desc="FAIRY PLATINUM PLUS DISHES 650ml",
             qty=2, unit="τεμ", unit_price=2.36,
             net=4.72, vat_pct=6, vat_amt=0.28, gross=5.00),
        dict(desc="DETTOL SPRAY ΑΝΤΙΒΑΚΤΗΡΙΔΙΑΚΟ 750ml",
             qty=1, unit="τεμ", unit_price=3.77,
             net=3.77, vat_pct=6, vat_amt=0.23, gross=4.00),
        # @24%
        dict(desc="ARIEL PODS ALL-IN-1 40 τεμ",
             qty=1, unit="τεμ", unit_price=8.06,
             net=8.06, vat_pct=24, vat_amt=1.94, gross=10.00),
        dict(desc="VANISH GOLD SPRAY 500ml",
             qty=1, unit="τεμ", unit_price=6.45,
             net=6.45, vat_pct=24, vat_amt=1.55, gross=8.00),
        dict(desc="SWIFFER SWEEPER ΑΝΤΑΛΛΑΚΤΙΚΑ x8",
             qty=1, unit="τεμ", unit_price=8.87,
             net=8.87, vat_pct=24, vat_amt=2.13, gross=11.00),
    ]
    make_invoice(
        "TC14_metro_cleaning_only.pdf",
        "ΤΙΜΟΛΟΓΙΟ ΑΓΟΡΑΣ",
        "ΤΤ-0024709", "05/02/2026",
        seller, buyer, items,
        note="Αγορά ειδών καθαριότητας — Κατάστημα ΜΕΤΡΟ Αθηνών (ΚΕΝΤΡΙΚΟ)",
    )


# ── TC15: METRO FOOD — ΑΓΓΕΛΑΚΗ (Thessaloniki) ───────────────────────────────
# Supplier: METRO ΑΕΒΕ | AFM: 094062259 | Code: 50.00.02732
# Branch:   ΑΓΓΕΛΑΚΗ (Thessaloniki)
# Account:  60.02.00002 (ΑΓΓΕΛΑΚΗ) — different from ΚΕΝΤΡΙΚΟ's 60.02.00000
# Tests branch detection: buyer address shows Thessaloniki branch
# All food @13%

def tc15():
    seller = dict(
        name="ΜΕΤΡΟ ΑΕΒΕ",
        afm="094062259",
        doy="ΦΑΕ ΑΘΗΝΩΝ",
        addr="Σπ. Πάτση 6 & Αγ. Αναργύρων, 121 31 Αθήνα",
        phone="210-5198000",
    )
    # Buyer address is Thessaloniki branch — key clue for branch detection
    buyer = dict(PROPORIA,
                 addr="Λ. Γεωργικής Σχολής 65, 541 28 Θεσσαλονίκη — ΥΠΟΚ/ΜΑ ΑΓΓΕΛΑΚΗ")
    items = [
        dict(desc="NESCAFE 3in1 CLASSIC 10 ΦΑΚΕΛΑΚΙΑ",
             qty=5, unit="τεμ", unit_price=1.06,
             net=5.31, vat_pct=13, vat_amt=0.69, gross=6.00),
        dict(desc="ΒΟΥΤΥΡΟ LURPAK ΑΠΑΛΟ 250γρ",
             qty=2, unit="τεμ", unit_price=2.65,
             net=5.31, vat_pct=13, vat_amt=0.69, gross=6.00),
        dict(desc="ΣΟΚΟΛΑΤΑ LACTA ΚΛΑΣΣΙΚΗ 100γρ",
             qty=3, unit="τεμ", unit_price=1.18,
             net=3.54, vat_pct=13, vat_amt=0.46, gross=4.00),
        dict(desc="ΛΕΜΟΝΑΔΑ ΒΕΒΕΝΤΑ 1,5L",
             qty=6, unit="τεμ", unit_price=0.89,
             net=5.31, vat_pct=13, vat_amt=0.69, gross=6.00),
    ]
    make_invoice(
        "TC15_metro_food_aggel.pdf",
        "ΤΙΜΟΛΟΓΙΟ ΑΓΟΡΑΣ",
        "ΤΤ-0024818", "07/02/2026",
        seller, buyer, items,
        note="Αγορά ειδών κυλικείου — Κατάστημα ΜΕΤΡΟ Θεσσαλονίκης",
    )


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating test PDFs...")
    tc1()
    tc2()
    tc3()
    tc4()
    tc5()
    tc6()
    tc7()
    tc8()
    tc9()
    tc10()
    tc11()
    tc12()
    tc13()
    tc14()
    tc15()
    print("\nAll PDFs written to: tests/pdfs/")
    print("\nTest summary:")
    print("  TC1  fuel_milos          - Fuel ΜΗΛΟΣ, ΞΥΔΟΥΣ, 1 item @24%")
    print("  TC2  repair_mykonos      - Vehicle repair ΜΥΚΟΝΟΣ, ICAR, 3 items @24%")
    print("  TC3  telecom_maroussi    - Telecom ΜΑΡΟΥΣΙ, NOVA, 2 items @24%")
    print("  TC4  metro_food_only     - METRO food ΚΕΝΤΡΙΚΟ, 6 items @13%+@24% [non-deductible VAT]")
    print("  TC5  metro_mixed         - METRO food+cleaning ΚΕΝΤΡΙΚΟ, 9 items [split + VAT summary trap]")
    print("  TC6  deh_electricity     - Electricity ΚΕΝΤΡΙΚΟ, ΔΕΗ, @6%")
    print("  TC7  rainbow_water       - Water ΚΕΝΤΡΙΚΟ, RAINBOW, @13%")
    print("  TC8  coral_fuel_corfu    - Fuel ΚΕΡΚΥΡΑ, CORAL, @24%")
    print("  TC9  meidanis_repair     - Vehicle repair ΚΕΝΤΡΙΚΟ, ΜΕΙΔΑΝΗΣ, @24%")
    print("  TC10 botos_repair_corfu  - Vehicle repair ΚΕΡΚΥΡΑ, ΜΠΟΤΟΣ, @24%")
    print("  TC11 eurobank_leasing    - Leasing EUROBANK, capital @0% + interest @24%")
    print("  TC12 generali_insurance  - Insurance GENERALI, no VAT")
    print("  TC13 bank_road_tax       - Bank payment road tax, no supplier")
    print("  TC14 metro_cleaning_only - METRO cleaning ΚΕΝΤΡΙΚΟ, @6%+@24% [deductible VAT]")
    print("  TC15 metro_food_aggel    - METRO food ΑΓΓΕΛΑΚΗ branch @13%")
