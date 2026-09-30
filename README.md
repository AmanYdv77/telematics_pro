# 🚗 TelematicsPro - Vehicle Telematics Data Pipeline

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://telematicspro.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red.svg)](https://streamlit.io/)
[![CI](https://github.com/AmanYdv77/telematics_pro/actions/workflows/ci.yml/badge.svg)](https://github.com/AmanYdv77/telematics_pro/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A professional-grade Streamlit web application for uploading, inspecting, mapping, cleaning, and analyzing raw vehicle telematics data.

🔗 **Live Application:** [telematicspro.streamlit.app](https://telematicspro.streamlit.app/)

---

## ✨ Features

- 📁 **Stage 1: Upload & Inspect** — Upload CSV files, rich column analysis with distribution histograms and data quality flags.
- 🔗 **Stage 2: Map & Parse** — Map raw columns to 40+ standard telematics features and parse complex encoded fields (JSON, delimiters, accelerometer vectors).
- ⚙️ **Stage 3: Segment & Extract** — Automatic trip segmentation based on temporal gaps, with customizable kinematic and spatial feature extraction.
- 🧹 **Stage 4: Clean** — Per-column cleaning with missing value imputation strategies and configurable outlier treatment (IQR, Z-Score).
- 📊 **Stage 5: Analyze** — Interactive Plotly charts, correlation matrices, trip analytics, and comprehensive data profiling.
- 💾 **Stage 6: Export** — Export cleaned CSV datasets alongside an automated data processing audit report.

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** — [Download from python.org](https://python.org/)

### Local Installation

#### Windows
```cmd
setup.bat
run.bat
```

#### macOS / Linux
```bash
chmod +x setup.sh run.sh
./setup.sh
./run.sh
```

#### Manual Setup
```bash
# Clone the repository
git clone https://github.com/AmanYdv77/telematics_pro.git
cd telematics_pro

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Unix or MacOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Launch application
streamlit run app.py
```

Then open `http://localhost:8501` in your browser.

---

## 📂 Project Structure

```text
streamlit_telematics/
├── app.py                 # Main Streamlit web application
├── requirements.txt       # Production dependencies
├── setup.bat              # Windows setup script
├── setup.sh               # Mac/Linux setup script
├── run.bat                # Windows run script
├── run.sh                 # Mac/Linux run script
├── src/
│   ├── constants.py       # Standard features, thresholds, and configuration
│   ├── engine.py          # Core transformation and extraction algorithms
│   ├── sample_data.py     # Sample telematics data generator
│   └── utils.py           # Helper and plotting utility functions
└── README.md
```

---

## 📊 File Size & Performance Recommendations

| File Size | Approximate Rows | Performance |
|---|---|---|
| `< 50 MB` | `< 250,000` | ⚡ Excellent |
| `50 - 100 MB` | `250,000 - 500,000` | ✅ Good |
| `100 - 200 MB` | `500,000 - 1,000,000` | ⚠️ Moderate |
| `> 200 MB` | `> 1,000,000` | ❌ Chunked/sampled processing recommended |

---

## 🔧 Configuration

Edit `src/constants.py` to customize:
- Standard feature mappings and aliases
- Harsh braking and rapid acceleration G-force thresholds
- Trip gap duration cutoff (seconds)
- File size thresholds

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
