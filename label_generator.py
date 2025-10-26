#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Label generation module for LEITZ binder spine labels.
Uses Jinja2 templates for flexible label design.
"""

import os
import yaml
from typing import List, Dict, Any
from io import BytesIO
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import Color, black, white, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class LabelGenerator:
    """Generates LEITZ binder spine labels from configuration and data."""
    
    def __init__(self, config: Dict[str, Any], template_dir: str = None):
        """
        Initialize the label generator with configuration.
        
        Args:
            config: Dictionary containing style and category configuration
            template_dir: Directory containing Jinja2 label templates
        """
        self.config = config
        self.style = config["style"]
        self.categories = config.get("categories", {})
        self.fonts_registered = False
        
        # Setup Jinja2 environment
        if template_dir is None:
            template_dir = Path(__file__).parent / "label_templates"
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))
    
    @classmethod
    def from_yaml(cls, yaml_path: str, template_dir: str = None):
        """Load configuration from YAML file and create generator."""
        with open(yaml_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return cls(config, template_dir)
    
    def render_label_template(self, category: str, short_code: str, start_year: int, 
                             subcategories: List[str], format_name: str) -> str:
        """
        Render a label using Jinja2 template.
        
        Args:
            category: Category name
            short_code: Short code for the binder
            start_year: Starting year
            subcategories: List of subcategory strings
            format_name: Format name (schmal, mittel, breit, extra)
        
        Returns:
            Rendered template string
        """
        template = self.jinja_env.get_template("binder_label.jinja2")
        
        # Get label dimensions from new label_sizes structure
        label_sizes = self.style.get("label_sizes", {})
        format_config = label_sizes.get(format_name, {"width_mm": 38, "height_mm": 285})
        width_mm = format_config.get("width_mm", 38)
        height_mm = format_config.get("height_mm", 285)
        
        base_color = self.get_base_color(category)
        accent_color = self.get_accent_color(category, start_year)
        accent_color_hex = self.color_to_hex(accent_color)  # Convert to hex for HTML
        
        # Check if this is an emergency category
        cat_info = self.categories.get(category, {})
        is_emergency = cat_info.get("is_emergency", False)
        emergency_text = self.style.get("emergency_text", "NOTFALL")
        
        context = {
            "category": category,
            "short_code": short_code,
            "start_year": start_year,
            "subcategories": subcategories,
            "format": format_name,
            "base_color": base_color,
            "accent_color": accent_color_hex,  # Use hex string for HTML
            "width_mm": width_mm,
            "height_mm": height_mm,
            "is_emergency": is_emergency,
            "emergency_text": emergency_text,
            "style": self.style
        }
        
        return template.render(**context)
    
    def register_fonts(self):
        """Register custom fonts if available."""
        if self.fonts_registered:
            return
        
        try:
            pdfmetrics.registerFont(TTFont("DejaVuSans", self.style["font_path_regular"]))
            pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", self.style["font_path_bold"]))
            self.fonts_registered = True
        except Exception as e:
            print(f"Warning: Could not register custom fonts: {e}")
            # Fall back to default fonts
            self.style["font_regular"] = "Helvetica"
            self.style["font_bold"] = "Helvetica-Bold"
            self.fonts_registered = True
    
    def get_text_contrast_color(self, bg_color: Color) -> Color:
        """Get contrasting text color (black or white) based on background luminance."""
        # Calculate relative luminance
        luminance = 0.299 * bg_color.red + 0.587 * bg_color.green + 0.114 * bg_color.blue
        # Return black for light backgrounds, white for dark backgrounds
        return black if luminance > 0.5 else white
    
    def color_to_hex(self, color: Color) -> str:
        """Convert ReportLab Color object to hex string for HTML."""
        r = int(color.red * 255)
        g = int(color.green * 255)
        b = int(color.blue * 255)
        return "#%02x%02x%02x" % (r, g, b)
    
    def clamp(self, v, lo, hi):
        """Clamp value between lo and hi."""
        return max(lo, min(hi, v))
    
    def mix_to_white(self, hex_color: str, t: float) -> Color:
        """Mix a hex color toward white by factor t (0=original, 1=white)."""
        base = HexColor(hex_color)
        r, g, b = base.red, base.green, base.blue
        r2 = r + (1 - r) * t
        g2 = g + (1 - g) * t
        b2 = b + (1 - b) * t
        return Color(r2, g2, b2)
    
    def hash_color_from_string(self, name: str) -> str:
        """Generate a consistent color from a string name."""
        import hashlib
        h = int(hashlib.sha1(name.encode("utf-8")).hexdigest()[:8], 16)
        H = (h % 36000) / 100.0
        S = 0.45 + ((h >> 8) % 2000) / 2000.0 * 0.20
        L = 0.45 + ((h >> 16) % 1500) / 1500.0 * 0.15
        return self._hsl_to_hex(H, S, L)
    
    def _hsl_to_hex(self, h, s, l) -> str:
        """Convert HSL to hex color."""
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
    
    def get_base_color(self, cat: str) -> str:
        """Get base color for a category."""
        return self.categories.get(cat, {}).get("base_color", self.hash_color_from_string(cat))
    
    def get_accent_color(self, cat: str, start_year: int) -> Color:
        """Get accent color based on category and year (gradient to white for newer years)."""
        year_min = self.style["year_min"]
        year_max = self.style["year_max"]
        base_hex = self.get_base_color(cat)
        
        # Emergency categories don't get year-based gradient
        cat_info = self.categories.get(cat, {})
        if cat_info.get("is_emergency", False):
            return HexColor(base_hex)
        
        t = self.clamp((start_year - year_min) / float(year_max - year_min), 0.0, 1.0)
        return self.mix_to_white(base_hex, t)
    
    def draw_wrapped_text(self, c: canvas.Canvas, x, y, w, text, font_name, font_size, leading=None):
        """Draw text with word wrapping."""
        if leading is None:
            leading = font_size * 1.15
        words = text.split()
        line = ""
        for word in words:
            test = (line + " " + word).strip()
            if pdfmetrics.stringWidth(test, font_name, font_size) <= w:
                line = test
            else:
                c.drawString(x, y, line)
                y -= leading
                line = word
        if line:
            c.drawString(x, y, line)
        return y
    
    def draw_label(self, c, x0, y0, w_mm, h_mm, cat, short, year, subcats):
        """Draw a single label on the canvas."""
        w = w_mm * mm
        h = h_mm * mm
        pad = self.style["padding"] * mm
    
        accent = self.get_accent_color(cat, year)
        base = HexColor(self.get_base_color(cat))
        
        # Check if category is marked as emergency
        cat_info = self.categories.get(cat, {})
        is_emergency = cat_info.get("is_emergency", False)
    
        # Border
        c.setStrokeColor(black)
        c.rect(x0, y0, w, h, stroke=1, fill=0)
    
        # Emergency border (if category is marked as emergency)
        if is_emergency:
            c.setStrokeColor(base)
            c.setLineWidth(self.style.get("notfall_border_mm", 3) * mm / 3.0)
            c.rect(x0 + 1.2, y0 + 1.2, w - 2.4, h - 2.4, stroke=1, fill=0)
    
        # Top bar
        bar_h = self.style["top_bar_height_mm"] * mm
        c.setFillColor(accent)
        c.rect(x0, y0 + h - bar_h, w, bar_h, stroke=0, fill=1)
    
        # Use contrast color for text on colored background
        text_color = self.get_text_contrast_color(accent)
        c.setFillColor(text_color)
        c.setFont(self.style["font_bold"], self.style["font_size_header"])
        c.drawString(x0 + pad, y0 + h - bar_h + pad + 7, cat)
        c.setFont(self.style["font_regular"], self.style["font_size_subheader"])
        c.drawString(x0 + pad, y0 + h - bar_h + pad - 2, f"{short}-{year}")
    
        # Content area
        y_text = y0 + h - bar_h - 8 * mm
        c.setFillColor(black)
        c.setFont(self.style["font_bold"], self.style["font_size_body"])
        c.drawString(x0 + pad, y_text, "Contents:")
        c.setFont(self.style["font_regular"], self.style["font_size_body"] - 1)
        y_text -= 10
        # Limit to 5 subcategories for 150mm height
        for s in subcats[:5]:
            c.drawString(x0 + pad, y_text, f"• {s}")
            y_text -= 9
            if y_text < y0 + 60:
                break
    
        # Timeline - Vertical with circles
        timeline_x = x0 + w / 2
        timeline_start_y = y0 + 30
        circle_radius = 3 * mm
        circle_gap = 12 * mm
        
        c.setFont(self.style["font_regular"], 7)
        # First circle with year label
        c.circle(timeline_x, timeline_start_y, circle_radius, stroke=1, fill=0)
        c.setFont(self.style["font_bold"], 7)
        c.drawCentredString(timeline_x, timeline_start_y - 5 * mm, str(year))
        
        # Additional circles with blank lines
        c.setFont(self.style["font_regular"], 6)
        for i in range(1, 4):
            y_pos = timeline_start_y + (i * circle_gap)
            c.circle(timeline_x, y_pos, circle_radius, stroke=1, fill=0)
            # Draw blank line for handwriting
            c.setStrokeColor(Color(0.8, 0.8, 0.8))
            c.setLineWidth(0.5)
            c.line(timeline_x - 7.5 * mm, y_pos - 3 * mm, timeline_x + 7.5 * mm, y_pos - 3 * mm)
            c.setStrokeColor(black)
    
        # Emergency text
        if is_emergency:
            c.setFont(self.style["font_bold"], 5)
            c.setFillColor(black)
            # Get emergency text from config
            emergency_text = self.style.get("emergency_text", "IN CASE OF EMERGENCY:\nTake this binder when leaving due to fire or flood!")
            lines = emergency_text.split("\n")
            # Position in middle area, limit to 4 lines
            cy = y0 + h * 0.45
            for i, line in enumerate(lines[:4]):
                if len(line) > 35:  # Truncate long lines
                    line = line[:32] + "..."
                c.drawCentredString(x0 + w / 2, cy - i * 6, line)
    
    def paginate_and_draw(self, df, c):
        """Paginate labels and draw them on the canvas."""
        page_w, page_h = A4
        left = self.style["page_margin_l_mm"] * mm
        right = self.style["page_margin_r_mm"] * mm
        top = self.style.get("page_margin_t_mm", 15) * mm
        
        # Get label_sizes or fall back to old formats_mm for backward compatibility
        label_sizes = self.style.get("label_sizes", {})
        if not label_sizes and "formats_mm" in self.style:
            # Backward compatibility: convert old formats_mm to label_sizes structure
            label_sizes = {
                fmt: {"width_mm": width, "height_mm": self.style.get("label_height_mm", 285)}
                for fmt, width in self.style["formats_mm"].items()
            }
        
        # Default height if not specified
        default_height = self.style.get("label_height_mm", 285)
        
        gutter = self.style["gutter_x_mm"] * mm
        x = left
    
        for _, row in df.iterrows():
            fmt = str(row.get("Format", "schmal")).strip().lower()
            
            # Get dimensions from label_sizes
            format_config = label_sizes.get(fmt, {"width_mm": 38, "height_mm": default_height})
            w_mm = format_config.get("width_mm", 38)
            h_mm = format_config.get("height_mm", default_height)
            
            if x + w_mm * mm > page_w - right:
                c.showPage()
                x = left
            
            # Position labels from top instead of bottom
            y_position = page_h - top - h_mm * mm
            
            sub = str(row.get("Subcategories", "")).replace(",", ";").split(";")
            sub = [s.strip() for s in sub if s.strip()]
            self.draw_label(
                c,
                x,
                y_position,
                w_mm,
                h_mm,
                row["Category"],
                row["ShortCode"],
                int(row["StartYear"]),
                sub,
            )
            x += w_mm * mm + gutter
    
    def generate_pdf(self, df: pd.DataFrame, output_path: str = None) -> bytes:
        """
        Generate PDF from dataframe.
        
        Args:
            df: DataFrame with columns: Category, ShortCode, StartYear, Subcategories, Format
            output_path: Optional path to save PDF file. If None, returns bytes only.
        
        Returns:
            PDF content as bytes
        """
        self.register_fonts()
        
        if output_path:
            c = canvas.Canvas(output_path, pagesize=A4)
            self.paginate_and_draw(df, c)
            c.save()
            
            with open(output_path, 'rb') as f:
                return f.read()
        else:
            # Generate in memory
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            self.paginate_and_draw(df, c)
            c.save()
            return buffer.getvalue()
