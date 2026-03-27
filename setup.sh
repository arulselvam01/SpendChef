#!/bin/bash
# setup.sh - Installation script for Streamlit Cloud

echo "Setting up SpendChef..."

# Update package list
apt-get update

# Install Tesseract OCR
apt-get install -y tesseract-ocr tesseract-ocr-eng libtesseract-dev

# Verify installation
tesseract --version

echo "Setup completed successfully!"