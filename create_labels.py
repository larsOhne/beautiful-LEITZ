#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generates standardized LEITZ binder spine labels from an Excel input file.
All style parameters, dimensions, and category colors are loaded from a YAML config.

Input:
    Excel file with columns:
        Category, ShortCode, StartYear, Subcategories, Format

Output:
    A4 PDF with as many labels per page as fit horizontally.

Dependencies:
    pip install pandas reportlab pyyaml
"""

import math
import pathlib
import yaml
from typing import List

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import Color, black, white, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ------------------------------------------------------------
# Load configuration
# ------------------------------------------------------------

CONFIG_FILE = "label_config.yaml"
INPUT_XLSX = "binder_labels.xlsx"
OUTPUT_PDF = "leitz_labels.pdf"


def load_config(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


cfg = load_config(CONFIG_FILE)

STYLE = cfg["style"]
CATEGORIES = cfg["categories"]

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def mix_to_white(hex_color: str, t: float) -> Color:
    base = HexColor(hex_color)
    r, g, b = base.red, base.green, base.blue
    r2 = r + (1 - r) * t
    g2 = g + (1 - g) * t
    b2 = b + (1 - b) * t
    return Color(r2, g2, b2)

def hash_color_from_string(name: str) -> str:
    import hashlib
    h = int(hashlib.sha1(name.encode("utf-8")).hexdigest()[:8], 16)
    H = (h % 36000) / 100.0
    S = 0.45 + ((h >> 8) % 2000) / 2000.0 * 0.20
    L = 0.45 + ((h >> 16) % 1500) / 1500.0 * 0.15
    return _hsl_to_hex(H, S, L)

def _hsl_to_hex(h, s, l) -> str:
    c = (1 - abs(2*l - 1)) * s
    x = c * (1 - abs(((h/60) % 2) - 1))
    m = l - c/2
    if 0 <= h < 60:   r1, g1, b1 = c, x, 0
    elif 60 <= h < 120: r1, g1, b1 = x, c, 0
    elif 120 <= h < 180: r1, g1, b1 = 0, c, x
    elif 180 <= h < 240: r1, g1, b1 = 0, x, c
    elif 240 <= h < 300: r1, g1, b1 = x, 0, c
    else:                r1, g1, b1 = c, 0, x
    r, g, b = (r1 + m), (g1 + m), (b1 + m)
    return "#%02x%02x%02x" % (int(r*255), int(g*255), int(b*255))

def get_base_color(cat: str) -> str:
    return CATEGORIES.get(cat, {}).get("base_color", hash_color_from_string(cat))

def get_accent_color(cat: str, start_year: int) -> Color:
    year_min = STYLE["year_min"]
    year_max = STYLE["year_max"]
    base_hex = get_base_color(cat)
    if cat.lower() == "notfall":
        return HexColor(base_hex)
    t = clamp((start_year - year_min) / float(year_max - year_min), 0.0, 1.0)
    return mix_to_white(base_hex, t)

def draw_wrapped_text(c: canvas.Canvas, x, y, w, text, font_name, font_size, leading=None):
    if leading is None:
        leading = font_size * 1.15
    words = text.split()
    line = ""
    for wword in words:
        test = (line + " " + wword).strip()
        if pdfmetrics.stringWidth(test, font_name, font_size) <= w:
            line = test
        else:
            c.drawString(x, y, line)
            y -= leading
            line = wword
    if line:
        c.drawString(x, y, line)
    return y

# ------------------------------------------------------------
# Draw label
# ------------------------------------------------------------

def draw_label(c, x0, y0, w_mm, h_mm, cat, short, year, subcats):
    w = w_mm * mm
    h = h_mm * mm
    pad = STYLE["padding"] * mm

    accent = get_accent_color(cat, year)
    base = HexColor(get_base_color(cat))

    # Border
    c.setStrokeColor(black)
    c.rect(x0, y0, w, h, stroke=1, fill=0)

    if cat.lower() == "notfall":
        c.setStrokeColor(base)
        c.setLineWidth(STYLE["notfall_border_mm"] * mm / 3.0)
        c.rect(x0 + 1.2, y0 + 1.2, w - 2.4, h - 2.4, stroke=1, fill=0)

    # Top bar
    bar_h = STYLE["top_bar_height_mm"] * mm
    c.setFillColor(accent)
    c.rect(x0, y0 + h - bar_h, w, bar_h, stroke=0, fill=1)

    c.setFillColor(white)
    c.setFont(STYLE["font_bold"], STYLE["font_size_header"])
    c.drawString(x0 + pad, y0 + h - bar_h + pad + 7, cat)
    c.setFont(STYLE["font_regular"], STYLE["font_size_subheader"])
    c.drawString(x0 + pad, y0 + h - bar_h + pad - 2, f"{short}-{year}")

    # Content area
    y_text = y0 + h - bar_h - 8 * mm
    c.setFillColor(black)
    c.setFont(STYLE["font_bold"], STYLE["font_size_body"])
    c.drawString(x0 + pad, y_text, "Contents:")
    c.setFont(STYLE["font_regular"], STYLE["font_size_body"] - 1)
    y_text -= 12
    for s in subcats:
        c.drawString(x0 + pad, y_text, f"• {s}")
        y_text -= 11
        if y_text < y0 + 50:
            break

    # Timeline
    y_line = y0 + 25
    c.setFont(STYLE["font_regular"], 9)
    c.drawString(x0 + pad, y_line + 15, f"Start: {year}")
    box_w = 15
    gap = 3
    bx = x0 + pad
    for i in range(11):
        c.rect(bx, y_line, box_w, 10, stroke=1, fill=0)
        if i % 2 == 0:
            c.drawString(bx + 3, y_line - 8, str(year + i))
        bx += box_w + gap

    # Emergency special
    if cat.lower() == "notfall":
        c.setFont(STYLE["font_bold"], 9)
        c.setFillColor(black)
        msg = "IN CASE OF EMERGENCY:\nTake this binder when leaving due to fire or flood!"
        lines = msg.split("\n")
        cy = y0 + h * 0.4
        for i, line in enumerate(lines):
            c.drawCentredString(x0 + w / 2, cy - i * 12, line)

# ------------------------------------------------------------
# Pagination
# ------------------------------------------------------------

def paginate_and_draw(df, c):
    page_w, page_h = A4
    left = STYLE["page_margin_l_mm"] * mm
    right = STYLE["page_margin_r_mm"] * mm
    bottom = STYLE["page_margin_b_mm"] * mm
    label_h = STYLE["label_height_mm"] * mm
    gutter = STYLE["gutter_x_mm"] * mm
    x = left

    for _, row in df.iterrows():
        fmt = str(row.get("Format", "schmal")).strip().lower()
        w_mm = STYLE["formats_mm"].get(fmt, 38)
        if x + w_mm * mm > page_w - right:
            c.showPage()
            x = left
        sub = str(row.get("Subcategories", "")).replace(",", ";").split(";")
        sub = [s.strip() for s in sub if s.strip()]
        draw_label(
            c,
            x,
            bottom,
            w_mm,
            STYLE["label_height_mm"],
            row["Category"],
            row["ShortCode"],
            int(row["StartYear"]),
            sub,
        )
        x += w_mm * mm + gutter

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def register_fonts():
    try:
        pdfmetrics.registerFont(TTFont("DejaVuSans", STYLE["font_path_regular"]))
        pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", STYLE["font_path_bold"]))
    except Exception:
        pass

def main():
    in_path = pathlib.Path(INPUT_XLSX)
    if not in_path.exists():
        sample = pd.DataFrame({
            "Category": ["Finance", "Insurance", "Notfall", "Projects"],
            "ShortCode": ["FIN", "INS", "ICE", "PRJ"],
            "StartYear": [2012, 2004, 2020, 1999],
            "Subcategories": [
                "Taxes;Payroll;Bank",
                "Liability;Home;Car",
                "Passports;Certificates;Insurance IDs",
                "Building permit;Offers;Invoices"
            ],
            "Format": ["schmal", "breit", "schmal", "extra"],
        })
        sample.to_excel(in_path, index=False)

    df = pd.read_excel(in_path)
    register_fonts()

    c = canvas.Canvas(OUTPUT_PDF, pagesize=A4)
    paginate_and_draw(df, c)
    c.save()
    print(f"Generated: {OUTPUT_PDF}")
    print(f"Input: {INPUT_XLSX} (sample created if missing)")
    print(f"Config: {CONFIG_FILE}")

if __name__ == "__main__":
    main()
