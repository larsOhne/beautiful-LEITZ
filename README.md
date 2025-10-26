# beautiful-LEITZ 🏷️

**A beautiful web-based label generator for LEITZ binder spines.**

Generate professional, color-coded labels for your LEITZ binders with an easy-to-use web interface. Customize colors, manage categories, and create perfectly formatted A4 PDFs ready for printing.

---

## ✨ Features

- 🌐 **Web Interface** - Easy-to-use browser-based label management
- 🎨 **Customizable Colors** - Define your own category colors and styles
- 📊 **CSV Storage** - Simple CSV format for easy editing and version control
- 🖨️ **Print-Ready PDFs** - Generate A4 PDFs optimized for printing
- 💾 **Local Data Storage** - All settings and labels saved in ignored `data/` folder
- 🚨 **Emergency Labels** - Special styling for "Notfall" (emergency) binders
- 📅 **Year-Based Gradients** - Automatic color interpolation based on start year
- ⏱️ **Timeline Tracking** - Built-in 10-year timeline on each label
- 📝 **Jinja2 Templates** - Editable label templates for custom designs

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Web Interface

```bash
python app.py
```

The data folder will be created automatically on first run with:
- `label_config.yaml` - Configuration settings
- `binder_labels.csv` - Sample labels

Then open your browser to: **http://127.0.0.1:5000**

---

## 📖 Usage

### Web Interface

1. **Launch the app**: `python app.py`
2. **Add labels**: Click "Add New Label" on the home page
3. **Customize settings**: Visit the Settings page to adjust colors and dimensions
4. **Preview**: Click "Preview PDF" to see your labels
5. **Print**: Open the preview and use Ctrl+P to print directly from your browser

### Managing Categories

- Navigate to **Settings** → **Categories & Colors**
- Add new categories with custom colors
- Delete unused categories
- Category colors are used as base colors with year-based interpolation

### Label Format Options

- **Schmal** (38mm) - Narrow binders
- **Mittel** (52mm) - Medium binders
- **Breit** (61mm) - Wide binders
- **Extra** (80mm) - Extra-wide binders

### Editing Label Templates

Label templates are stored in `label_templates/binder_label.jinja2`. You can edit this file to customize:
- Layout structure
- Text content
- Conditional sections
- Dynamic elements

---

## 📂 Project Structure

```
beautiful-LEITZ/
├── app.py                      # Flask web application
├── label_generator.py          # Core label generation logic
├── requirements.txt            # Python dependencies
├── templates/                  # Web UI templates
│   ├── base.html              # Base template
│   ├── index.html             # Home page (label management)
│   └── settings.html          # Settings editor
├── label_templates/           # Label design templates
│   └── binder_label.jinja2   # Editable label template
└── data/                       # Local data (git-ignored, auto-created)
    ├── label_config.yaml      # Configuration settings
    └── binder_labels.csv      # Your labels
```

---

## 📝 Label Layout

Each LEITZ binder label contains:

### 1. **Top Color Bar**
- Background in accent color (base color + year interpolation)
- Category name in white text
- Unique ID: `<ShortCode>-<StartYear>` (e.g., `FIN-2012`)

### 2. **Content Area**
- "Contents:" header
- Bullet-point list of subcategories
- Auto-wrapped text

### 3. **Timeline Section**
- Start year label
- 10 empty boxes for year tracking
- Year markers every other box

### 4. **Emergency Design** (Notfall category only)
- Red border highlighting
- No color interpolation (stays red)
- Emergency warning text
- Special "IN CASE OF EMERGENCY" message

---

## ⚙️ Configuration

Settings are stored in `data/label_config.yaml`:

### Style Settings
- Font sizes (header, subheader, body)
- Page margins and gutters
- Label dimensions
- Format widths
- Year range for color gradient

### Categories
- Category name
- Base color (hex)

Example:
```yaml
categories:
  Finance:
    base_color: "#2E7D32"
  Medical:
    base_color: "#6A1B9A"
```

---

## 🎨 Color Logic

Labels use a smart color system:

1. Each category has a **base color**
2. Label accent color = `base_color` → `white` interpolation
3. Interpolation factor based on start year:
   - `year_min` (1990) → Full base color
   - `year_max` (2030) → Nearly white
4. **Exception**: "Notfall" category always uses pure base color

---

## 🖨️ Printing Tips

1. Click **Preview PDF** in the web interface
2. Use browser's print function (Ctrl+P / Cmd+P)
3. Settings:
   - Paper: A4
   - Margins: Default
   - Scale: 100%
   - Background graphics: ON
4. Print or save as PDF

---

## 📦 Data Management

### Data Directory
- Created automatically on first run
- Location: `./data/`
- Git-ignored for privacy

### Files
- `label_config.yaml` - All settings
- `binder_labels.csv` - Your label data (CSV format)

### CSV Format
The CSV file has these columns:
- `Category` - Category name
- `ShortCode` - Short code (3-4 letters)
- `StartYear` - Starting year (integer)
- `Subcategories` - Semicolon-separated list
- `Format` - Format name (schmal/mittel/breit/extra)

### Backup
Simply copy the `data/` folder to backup all your labels and settings.

---

## 🛠️ Development

### Project Requirements
- Python 3.7+
- Flask (web framework)
- pandas (CSV handling)
- reportlab (PDF generation)
- PyYAML (config files)
- Jinja2 (templating, included with Flask)

### Running in Debug Mode
The web app runs in debug mode by default. Edit `app.py` to change this.

---

## 📄 License

See [LICENSE](LICENSE) file for details.

---

## 💡 Tips & Tricks

- **Batch editing**: Edit `data/binder_labels.csv` directly in Excel or text editor for bulk changes
- **CSV benefits**: Easy to version control, diff, and merge
- **Template customization**: Modify `label_templates/binder_label.jinja2` to change label design
- **Color harmony**: Use online color palette generators for pleasing color schemes
- **Year strategy**: Set `year_min`/`year_max` to your actual range for better gradients
- **Print test**: Generate a single label first to verify sizing
- **Custom fonts**: Edit font paths in settings to use system fonts

---

## 🤝 Contributing

Contributions welcome! Feel free to open issues or submit pull requests.

---

**Happy Organizing! 📋✨**  



