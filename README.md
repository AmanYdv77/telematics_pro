# 🚗 TelematicsPro - Python/Streamlit Version

A professional-grade Streamlit web application for uploading, inspecting, mapping, cleaning, and analyzing raw vehicle telematics data.

## ✨ Features

- **📁 Stage 1: Upload & Inspect** - Upload CSV files, rich column analysis with histograms and quality flags
- **🔗 Stage 2: Map & Parse** - Map columns to 40 standard telematics features, parse complex encoded fields
- **⚙️ Stage 3: Segment & Extract** - Automatic trip segmentation, user-controlled feature extraction
- **🧹 Stage 4: Clean** - Per-column cleaning with missing value strategies, outlier treatment
- **📊 Stage 5: Analyze** - Interactive charts, correlation analysis, data profiling
- **💾 Stage 6: Export** - Download cleaned CSV and processing report

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** - Download from https://python.org/

### Installation

#### Windows
```cmd
setup.bat
```

#### Mac/Linux
```bash
chmod +x setup.sh
./setup.sh
```

#### Manual Setup
```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

## 📁 Project Structure

```
streamlit_telematics/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── setup.bat             # Windows setup script
├── setup.sh              # Mac/Linux setup script
├── run.bat               # Windows run script
├── run.sh                # Mac/Linux run script
├── src/
│   ├── constants.py      # Standard features, thresholds
│   ├── engine.py         # Data processing functions
│   ├── sample_data.py    # Sample data generator
│   └── utils.py          # Utility functions
└── README.md
```

## 📊 File Size Recommendations

| File Size | Rows | Performance |
|-----------|------|-------------|
| < 50 MB | < 250,000 | ⚡ Excellent |
| 50-100 MB | 250,000-500,000 | ✅ Good |
| 100-200 MB | 500,000-1,000,000 | ⚠️ Moderate |
| > 200 MB | > 1,000,000 | ❌ Not recommended |

## 🔧 Configuration

Edit `src/constants.py` to modify:
- Standard feature names
- Harsh braking/acceleration thresholds
- Trip gap duration
- File size limits

## 📄 License

MIT License - Feel free to use and modify.
