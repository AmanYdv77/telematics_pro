#!/bin/bash

echo "========================================"
echo "  TelematicsPro - Python Setup Script"
echo "  Vehicle Telematics Data Pipeline"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python3 is not installed!${NC}"
    echo "Please install Python from: https://python.org/"
    exit 1
fi

echo -e "${GREEN}[OK]${NC} Python found: $(python3 --version)"
echo ""

# Create virtual environment
echo -e "${YELLOW}[1/3]${NC} Creating virtual environment..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to create virtual environment!${NC}"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Virtual environment created!"
echo ""

# Activate and install dependencies
echo -e "${YELLOW}[2/3]${NC} Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to install dependencies!${NC}"
    exit 1
fi
echo -e "${GREEN}[OK]${NC} Dependencies installed!"
echo ""

# Run the application
echo -e "${YELLOW}[3/3]${NC} Starting TelematicsPro..."
echo ""
echo "========================================"
echo "  Application is starting..."
echo "  Open your browser to:"
echo -e "  ${GREEN}http://localhost:8501${NC}"
echo "========================================"
echo ""
echo "Press Ctrl+C to stop the server."
echo ""
streamlit run app.py
