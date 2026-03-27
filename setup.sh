#!/bin/bash
# setup.sh - Installation script for Streamlit Cloud

# Install system dependencies
apt-get update
apt-get install -y tesseract-ocr tesseract-ocr-eng

# Install Python dependencies
pip install -r requirements.txt

echo "Setup completed successfully!"