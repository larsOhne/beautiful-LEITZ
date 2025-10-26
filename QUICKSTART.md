# 🚀 Quick Start Guide

## First Time Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the web application:**
   ```bash
   python app.py
   ```
   
   Or use the convenience script:
   ```bash
   ./run.sh
   ```

   **The `data/` folder will be created automatically with:**
   - `label_config.yaml` - Default configuration
   - `binder_labels.csv` - Sample labels

3. **Open your browser:**
   Navigate to: **http://127.0.0.1:5000**

---

## Creating Your First Label

1. On the home page, click **"➕ Add New Label"**

2. Fill in the form:
   - **Category**: Select from existing or type a new one
   - **Short Code**: 3-4 letter abbreviation (e.g., FIN, MED)
   - **Start Year**: The year this binder starts
   - **Subcategories**: List items separated by semicolons (e.g., `Taxes;Invoices;Receipts`)
   - **Format**: Choose your binder width

3. Click **"💾 Save Label"**

4. Click **"👁️ Preview PDF"** to see your label

5. Print directly from the browser (Ctrl+P)

---

## Customizing Colors

1. Go to **⚙️ Settings**

2. In the **Categories & Colors** section:
   - Click **"➕ Add Category"** to create new categories
   - Choose a base color using the color picker
   - Existing categories can be deleted

3. Click **"💾 Save All Settings"**

---

## Editing Label Templates

1. Open `label_templates/binder_label.jinja2` in a text editor

2. Modify the template structure using Jinja2 syntax

3. Available variables:
   - `category`, `short_code`, `start_year`
   - `subcategories` (list)
   - `format`, `width_mm`, `height_mm`
   - `base_color`, `accent_color`
   - `style` (config dict)

4. Save and restart the app to see changes

---

## Tips

- **Bulk editing**: Edit `data/binder_labels.csv` in Excel or any text editor for faster batch updates
- **CSV format**: Category,ShortCode,StartYear,Subcategories,Format
- **Backup**: Copy the entire `data/` folder to preserve your labels and settings
- **Print test**: Create one label first to verify it matches your binder size
- **Emergency labels**: Use category name "Notfall" for special emergency styling

---

## Troubleshooting

### Port already in use
If port 5000 is occupied, edit `app.py` and change:
```python
app.run(debug=True, host='127.0.0.1', port=5000)
```
to use a different port (e.g., `port=5001`).

### Data folder not created
Make sure you have write permissions in the project directory.

### Fonts not found
The app will fall back to Helvetica if DejaVu fonts aren't installed. To use custom fonts:
1. Install the fonts on your system
2. Update font paths in Settings

### PDF not generating
Check that all required packages are installed:
```bash
pip install -r requirements.txt
```

---

## Next Steps

- Explore the **Settings** page to customize dimensions and styles
- Add all your binders to create a complete set
- Customize the label template in `label_templates/binder_label.jinja2`
- Generate and print your labels!

**Need help?** Check the full [README.md](README.md) for detailed documentation.
