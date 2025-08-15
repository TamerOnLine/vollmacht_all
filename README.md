# 🧾 Dynamic PDF Forms Generator — vollmacht_all

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-orange?style=flat-square)
![ReportLab](https://img.shields.io/badge/PDF-ReportLab-green?style=flat-square)
![License](https://img.shields.io/github/license/TamerOnLine/vollmacht_all?style=flat-square)

A multilingual dynamic PDF form generator with a Streamlit frontend.  
Allows filling in data, validating required fields, digitally signing (draw or upload), and generating professionally formatted PDFs.

---

## ✨ Features
- 🎯 **Supports multiple forms** — e.g., Vollmacht, Obdachlosigkeit.
- 🌍 **Multilingual interface** (DE / AR / EN — PDF output always in German by default).
- 🖋️ **Digital signature** — draw directly in the browser or upload a signature image with cropping and scaling options.
- 📄 **Professional PDF creation** using [ReportLab](https://www.reportlab.com/).
- ⚙️ **Highly customizable** — via `schema.json` and translation files `i18n.*.json`.
- 🛠 **Automatic project setup** with `pro_venv.py` (virtual environment, requirements, VS Code, GitHub Actions).

---

## 📂 Project Structure

```
vollmacht_all/
│
├── app.py                # Streamlit frontend (main entry point)
├── main.py               # Safe launcher that re-executes inside venv
├── pro_venv.py           # Project and environment setup
├── modules/              # Helper modules (form loader, signature management…)
├── forms/                # Available forms
│   ├── vollmacht/        # “Power of Attorney” form
│   │   ├── schema.json
│   │   ├── i18n.ar.json
│   │   ├── i18n.de.json
│   │   ├── i18n.en.json
│   │   └── builder.py
│   └── obdachlosigkeit/  # “Notice of Homelessness” form
│       ├── schema.json
│       ├── i18n.ar.json
│       ├── i18n.de.json
│       ├── i18n.en.json
│       └── builder.py
│
├── requirements.txt
├── setup-config.json     # Project settings & default PDF options
└── README.md
```

---

## 🚀 Quick Start

> **Step 1:** Set up the environment and configure automatically

```bash
python pro_venv.py
```

> **Step 2:** Start the application

```bash
python main.py
```

The Streamlit interface will open in your browser (default port **8501**).  
From the sidebar, you can select:
- **UI language** (DE / AR / EN)
- **Form** to fill out

After filling in the form and signing, click **Create PDF** to download it.

---

## 🖋️ Adding a New Form

1. Create a new folder under `forms/` with a unique name (e.g., `forms/myform/`).
2. Inside it, add:
   - `schema.json` — defines fields and sections.
   - `i18n.de.json` (required) + optional additional language files (`ar`, `en`, etc.).
   - `builder.py` — Python code for PDF generation.
3. Run the app — the form will be detected automatically.

---

## 📦 Requirements

- Python 3.12+
- Packages listed in `requirements.txt`:
  - streamlit
  - reportlab
  - pillow
  - numpy
  - streamlit-drawable-canvas

---

## 🧪 GitHub Actions (optional)
Create a minimal CI workflow:

```bash
python pro_venv.py --ci create
```

This creates `.github/workflows/test-pro_venv.yml`.

---

## 📝 License
[MIT License](LICENSE) — free to use, modify, and distribute.

---
