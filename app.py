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
                "schmal": {"width_mm": 38, "height_mm": 285},
                "mittel": {"width_mm": 52, "height_mm": 285},
                "breit": {"width_mm": 61, "height_mm": 285},
                "extra": {"width_mm": 80, "height_mm": 285}
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
            "Format": ["schmal", "breit", "schmal", "extra"]
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
            save_config(config)
            return jsonify({"success": True, "message": "Configuration saved successfully"})
        except Exception as e:
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
            
            if 'index' in data:
                # Update existing label
                idx = data['index']
                for key in ['Category', 'ShortCode', 'StartYear', 'Subcategories', 'Format']:
                    if key in data:
                        df.at[idx, key] = data[key]
            else:
                # Add new label
                new_row = {
                    'Category': data.get('Category', ''),
                    'ShortCode': data.get('ShortCode', ''),
                    'StartYear': int(data.get('StartYear', 2020)),
                    'Subcategories': data.get('Subcategories', ''),
                    'Format': data.get('Format', 'schmal')
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            
            save_labels(df)
            return jsonify({"success": True, "message": "Label saved successfully"})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 400
    
    elif request.method == 'DELETE':
        try:
            idx = request.args.get('index', type=int)
            df = load_labels()
            df = df.drop(idx).reset_index(drop=True)
            save_labels(df)
            return jsonify({"success": True, "message": "Label deleted successfully"})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 400


@app.route('/api/category', methods=['POST', 'DELETE'])
def api_category():
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
    """Preview labels in browser (printable page)."""
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
        
        generator = LabelGenerator(config)
        pdf_bytes = generator.generate_pdf(df)
        
        return send_file(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=False,
            download_name='labels_preview.pdf'
        )
    except Exception as e:
        return f"Error generating preview: {str(e)}", 500


@app.route('/download')
def download():
    """Download labels as PDF."""
    try:
        config = load_config()
        df = load_labels()
        
        if df.empty:
            return "No labels to download. Please add some labels first.", 400
        
        generator = LabelGenerator(config)
        pdf_bytes = generator.generate_pdf(df)
        
        return send_file(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name='leitz_labels.pdf'
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
