#!/usr/bin/env bash

# Install Tesseract OCR on Render
apt-get update
apt-get install -y tesseract-ocr
apt-get install -y tesseract-ocr-eng

echo "✅ Tesseract installed successfully"
