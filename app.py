#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask web application for LEITZ binder label generation.
Provides a web interface to manage settings and create labels.
Uses CSV for label storage.
"""

import os
import pathlib
import yaml
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from io import BytesIO
from label_generator import LabelGenerator

app = Flask(__name__)

# Paths
DATA_DIR = pathlib.Path(__file__).parent / "data"
CONFIG_FILE = DATA_DIR / "label_config.yaml"
LABELS_FILE = DATA_DIR / "binder_labels.csv"


def ensure_data_directory():
    """
    Create data directory and default files if they don't exist.
    This runs programmatically on first execution.
    """
    # Create data directory
    DATA_DIR.mkdir(exist_ok=True)
    print(f"✓ Data directory ensured: {DATA_DIR}")
    
    # Create default config if it doesn't exist
    if not CONFIG_FILE.exists():
        default_config = {
            "style": {
                "font_regular": "Helvetica",
                "font_bold": "Helvetica-Bold",
                "font_path_regular": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "font_path_bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "font_size_header": 14,
                "font_size_subheader": 9,
                "font_size_body": 9,
                "page_margin_l_mm": 10,
                "page_margin_r_mm": 10,
                "page_margin_t_mm": 15,
                "page_margin_b_mm": 20,
                "gutter_x_mm": 3,
                "top_bar_height_mm": 30,
                "padding": 3,
                "emergency_border_mm": 2,
                "year_min": 1990,
                "year_max": 2030,
                "emergency_text": "IN CASE OF EMERGENCY:\nTake this binder when leaving due to fire or flood!"
            },
            "label_sizes": {
                "normal": {"width_mm": 58, "height_mm": 120}
            },
            "categories": {
                "Finance": {
                    "base_color": "#2E7D32",
                    "short_code": "FIN",
                    "is_emergency": False
                },
                "Insurance": {
                    "base_color": "#1565C0",
                    "short_code": "INS",
                    "is_emergency": False
                },
                "Notfall": {
                    "base_color": "#C62828",
                    "short_code": "ICE",
                    "is_emergency": True
                },
                "Projects": {
                    "base_color": "#F57C00",
                    "short_code": "PRJ",
                    "is_emergency": False
                },
                "Medical": {
                    "base_color": "#6A1B9A",
                    "short_code": "MED",
                    "is_emergency": False
                },
                "Legal": {
                    "base_color": "#455A64",
                    "short_code": "LEG",
                    "is_emergency": False
                }
            }
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
        print(f"✓ Created default config: {CONFIG_FILE}")
    
    # Create sample labels CSV if it doesn't exist
    if not LABELS_FILE.exists():
        sample_df = pd.DataFrame({
            "Category": ["Finance", "Insurance", "Notfall", "Projects"],
            "ShortCode": ["FIN", "INS", "ICE", "PRJ"],
            "StartYear": [2012, 2004, 2020, 1999],
            "Subcategories": [
                "Taxes;Payroll;Bank",
                "Liability;Home;Car",
                "Passports;Certificates;Insurance IDs",
                "Building permit;Offers;Invoices"
            ],
            "Format": ["normal", "normal", "normal", "normal"]
        })
        sample_df.to_csv(LABELS_FILE, index=False)
        print(f"✓ Created sample labels CSV: {LABELS_FILE}")


def load_config():
    """Load configuration from YAML file."""
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_config(config):
    """Save configuration to YAML file."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


def load_labels():
    """Load labels from CSV file."""
    if LABELS_FILE.exists():
        return pd.read_csv(LABELS_FILE)
    return pd.DataFrame(columns=["Category", "ShortCode", "StartYear", "Subcategories", "Format"])


def save_labels(df):
    """Save labels to CSV file."""
    df.to_csv(LABELS_FILE, index=False)


@app.route('/')
def index():
    """Home page."""
    config = load_config()
    df = load_labels()
    labels = df.to_dict('records') if not df.empty else []
    
    return render_template('index.html', 
                         labels=labels, 
                         config=config,
                         categories=list(config.get('categories', {}).keys()))


@app.route('/settings')
def settings():
    """Settings editor page."""
    config = load_config()
    return render_template('settings.html', config=config)


@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """API endpoint for getting/updating configuration."""
    if request.method == 'GET':
        config = load_config()
        return jsonify(config)
    
    elif request.method == 'POST':
        try:
            config = request.json
            print(f"[DEBUG] Saving config, emergency_text: {config['style'].get('emergency_text', 'NOT FOUND')[:50]}...")
            save_config(config)
            print(f"[DEBUG] Config saved to {CONFIG_FILE}")
            return jsonify({"success": True, "message": "Configuration saved successfully"})
        except Exception as e:
            print(f"[ERROR] Failed to save config: {e}")
            return jsonify({"success": False, "message": str(e)}), 400


@app.route('/api/labels', methods=['GET', 'POST', 'DELETE'])
def api_labels():
    """API endpoint for managing labels."""
    if request.method == 'GET':
        df = load_labels()
        return jsonify(df.to_dict('records'))
    
    elif request.method == 'POST':
        try:
            data = request.json
            df = load_labels()
            config = load_config()
            
            # Auto-generate ShortCode from category short_code + year
            category = data.get('Category', '')
            start_year = int(data.get('StartYear', 2020))
            
            # Get category short code from config
            category_short_code = config.get('categories', {}).get(category, {}).get('short_code', category[:3].upper())
            auto_short_code = f"{category_short_code}-{start_year}"
            
            # Get format, use first available if not specified
            format_value = data.get('Format')
            if not format_value or format_value not in config.get('label_sizes', {}):
                # Use first available format
                label_sizes = config.get('label_sizes', {})
                if label_sizes:
                    format_value = next(iter(label_sizes))
                else:
                    return jsonify({"success": False, "message": "No label sizes configured"}), 400
            
            if 'index' in data:
                # Update existing label
                idx = data['index']
                if idx < len(df):
                    df.at[idx, 'Category'] = category
                    df.at[idx, 'ShortCode'] = auto_short_code
                    df.at[idx, 'StartYear'] = start_year
                    df.at[idx, 'Subcategories'] = data.get('Subcategories', '')
                    df.at[idx, 'Format'] = format_value
                else:
                    return jsonify({"success": False, "message": "Invalid label index"}), 400
            else:
                # Add new label
                new_row = {
                    'Category': category,
                    'ShortCode': auto_short_code,
                    'StartYear': start_year,
                    'Subcategories': data.get('Subcategories', ''),
                    'Format': format_value
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            
            save_labels(df)
            return jsonify({"success": True, "message": "Label saved successfully"})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 400
    
    elif request.method == 'DELETE':
        try:
            idx = request.args.get('index', type=int)
            if idx is None:
                return jsonify({"success": False, "message": "No index provided"}), 400
            
            df = load_labels()
            
            if idx < 0 or idx >= len(df):
                return jsonify({"success": False, "message": "Invalid label index"}), 400
            
            df = df.drop(idx).reset_index(drop=True)
            save_labels(df)
            return jsonify({"success": True, "message": "Label deleted successfully"})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "message": str(e)}), 400


@app.route('/api/category', methods=['POST', 'DELETE'])
@app.route('/api/category/<category_name>', methods=['PUT'])
def api_category(category_name=None):
    """API endpoint for managing categories."""
    config = load_config()
    
    if request.method == 'POST':
        try:
            data = request.json
            name = data.get('name')
            color = data.get('color', '#000000')
            short_code = data.get('short_code', name[:3].upper())
            is_emergency = data.get('is_emergency', False)
            
            if not name:
                return jsonify({"success": False, "message": "Category name required"}), 400
            
            if 'categories' not in config:
                config['categories'] = {}
            
            config['categories'][name] = {
                "base_color": color,
                "short_code": short_code,
                "is_emergency": is_emergency
            }
            save_config(config)
            
            return jsonify({"success": True, "message": f"Category '{name}' added successfully"})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 400
    
    elif request.method == 'PUT':
        try:
            data = request.json
            new_name = data.get('name')
            color = data.get('color', '#000000')
            short_code = data.get('short_code', new_name[:3].upper())
            is_emergency = data.get('is_emergency', False)
            
            if not new_name:
                return jsonify({"success": False, "message": "Category name required"}), 400
            
            if category_name not in config.get('categories', {}):
                return jsonify({"success": False, "message": "Category not found"}), 404
            
            # If name changed, we need to update the key
            if category_name != new_name:
                # Check if new name already exists
                if new_name in config['categories']:
                    return jsonify({"success": False, "message": "A category with this name already exists"}), 400
                # Delete old entry
                del config['categories'][category_name]
            
            # Add/update the category with new values
            config['categories'][new_name] = {
                "base_color": color,
                "short_code": short_code,
                "is_emergency": is_emergency
            }
            save_config(config)
            
            return jsonify({"success": True, "message": f"Category '{new_name}' updated successfully"})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 400
    
    elif request.method == 'DELETE':
        try:
            name = request.args.get('name')
            if name in config.get('categories', {}):
                del config['categories'][name]
                save_config(config)
                return jsonify({"success": True, "message": f"Category '{name}' deleted successfully"})
            else:
                return jsonify({"success": False, "message": "Category not found"}), 404
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 400


@app.route('/preview')
def preview():
    """Preview labels in browser (printable page with HTML labels)."""
    try:
        config = load_config()
        df = load_labels()
        
        if df.empty:
            return "No labels to preview. Please add some labels first.", 400
        
        # Filter by checkbox selection if indices parameter is provided
        indices_param = request.args.get('indices')
        if indices_param:
            try:
                indices = [int(idx) for idx in indices_param.split(',')]
                df = df.iloc[indices]
            except (ValueError, IndexError) as e:
                return f"Invalid indices parameter: {str(e)}", 400
        
        # Generate HTML labels for browser printing
        generator = LabelGenerator(config)
        labels_html = []
        max_label_width = 0
        max_label_height = 0
        
        # Validate that we have at least one label size configured
        if not config.get('label_sizes'):
            return "No label sizes configured. Please add at least one label size in Settings.", 400
        
        # Get first available format as default fallback
        first_format = next(iter(config['label_sizes']))
        
        for _, row in df.iterrows():
            fmt = str(row.get("Format", first_format)).strip().lower()
            subcats = str(row.get("Subcategories", "")).replace(",", ";").split(";")
            subcats = [s.strip() for s in subcats if s.strip()]
            
            # Use first available format if requested format not found
            if fmt not in config['label_sizes']:
                fmt = first_format
            
            width = config['label_sizes'][fmt]['width_mm']
            height = config['label_sizes'][fmt]['height_mm']
            max_label_width = max(max_label_width, width)
            max_label_height = max(max_label_height, height)
            
            # Render each label using the HTML template
            label_html = generator.render_label_template(
                category=row["Category"],
                short_code=row["ShortCode"],
                start_year=int(row["StartYear"]),
                subcategories=subcats,
                format_name=fmt
            )
            labels_html.append(label_html)
        
        # Determine orientation based on label dimensions
        # If labels can fit 2 or more side-by-side in portrait, use portrait
        # Otherwise use landscape
        a4_portrait_width = 210  # mm
        a4_landscape_width = 297  # mm
        
        # Calculate how many labels fit side-by-side
        portrait_cols = int((a4_portrait_width - 20) / max_label_width)  # 20mm margins
        landscape_cols = int((a4_landscape_width - 20) / max_label_width)
        
        # Use landscape if it allows significantly more labels per row
        # Or if labels are too wide for portrait
        orientation = 'landscape' if (portrait_cols < 2 and landscape_cols >= 2) or max_label_width > 150 else 'portrait'
        
        # Render a print-ready page with all labels
        return render_template('print_labels.html', 
                             labels_html=labels_html, 
                             orientation=orientation,
                             label_width=max_label_width,
                             label_height=max_label_height)
        
    except Exception as e:
        return f"Error generating preview: {str(e)}", 500


@app.route('/download')
def download():
    """Download labels as PDF."""
    try:
        from datetime import datetime
        
        config = load_config()
        df = load_labels()
        
        if df.empty:
            return "No labels to download. Please add some labels first.", 400
        
        generator = LabelGenerator(config)
        pdf_bytes = generator.generate_pdf(df)
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'leitz_labels_{timestamp}.pdf'
        
        return send_file(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return f"Error generating PDF: {str(e)}", 500


if __name__ == '__main__':
    ensure_data_directory()
    print("\n" + "="*60)
    print("  LEITZ Label Generator - Web Interface")
    print("="*60)
    print(f"\n  Data directory: {DATA_DIR.absolute()}")
    print(f"  Config file:    {CONFIG_FILE.name}")
    print(f"  Labels file:    {LABELS_FILE.name}")
    print("\n  Open your browser and go to: http://127.0.0.1:5000")
    print("="*60 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5000)
