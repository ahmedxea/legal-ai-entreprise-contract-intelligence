# OCR Support - Deployment Guide

## Overview
The document extraction system now supports OCR (Optical Character Recognition) for:
- Scanned PDF documents (automatically detected)
- Image files (PNG, JPG, JPEG, TIF, TIFF, BMP)

## How It Works

### Automatic OCR Detection
When a PDF is uploaded, the system:
1. First attempts regular text extraction using pdfplumber
2. Calculates average characters per page
3. If < 100 characters/page, automatically applies OCR
4. Uses Tesseract OCR to extract text from scanned pages

### Direct Image Upload
Image files are processed directly with OCR:
- Supported formats: `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.bmp`
- Images are processed at 300 DPI for optimal accuracy
- Text extraction uses Tesseract with English language model

## Local Development Setup

### macOS
```bash
# Install system dependencies
brew install tesseract poppler

# Install Python packages (already in requirements.txt)
pip install pytesseract pdf2image Pillow==10.4.0

# Verify installation
tesseract --version
```

### Linux (Ubuntu/Debian)
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install tesseract-ocr poppler-utils

# Install Python packages
pip install pytesseract pdf2image Pillow==10.4.0
```

### Windows
```bash
# Install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
# Install Poppler from: https://github.com/oschwartz10612/poppler-windows/releases

# Add to PATH, then:
pip install pytesseract pdf2image Pillow==10.4.0
```

## Azure App Service Deployment

### Option 1: Using Custom Container (Recommended)
Create a custom Docker image with Tesseract and Poppler:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    tesseract-ocr \\
    tesseract-ocr-eng \\
    poppler-utils \\
    && rm -rf /var/lib/apt/lists/*

# Copy application
WORKDIR /app
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-azure.txt

# Start application
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-c", "gunicorn_config.py", "main:app"]
```

Deploy the container to Azure App Service:
```bash
# Build and push
docker build -t lexra-backend .
docker tag lexra-backend youracr.azurecr.io/lexra-backend:latest
docker push youracr.azurecr.io/lexra-backend:latest

# Deploy to App Service
az webapp config container set \\
    --name your-app-service \\
    --resource-group your-rg \\
    --docker-custom-image-name youracr.azurecr.io/lexra-backend:latest
```

### Option 2: Custom Startup Script
Add `azure-startup.sh` to install Tesseract during app startup:

```bash
#!/bin/bash
# Install Tesseract if not present
if ! command -v tesseract &> /dev/null; then
    echo "Installing Tesseract OCR..."
    apt-get update
    apt-get install -y tesseract-ocr poppler-utils
fi

# Start the application
gunicorn -k uvicorn.workers.UvicornWorker -c gunicorn_config.py main:app
```

Configure in Azure Portal:
1. Go to Configuration → General Settings
2. Set Startup Command: `bash azure-startup.sh`

**Note**: This requires root access and may not work on all App Service tiers.

### Option 3: Graceful Degradation (Current Approach)
The code already handles missing OCR gracefully:
- If Tesseract is not installed, regular PDF/DOCX extraction still works
- OCR-specific features (scanned PDFs, image uploads) will fail with clear error messages
- Error messages guide users to install OCR dependencies

## Configuration

### File Type Support
Updated in `backend/app/core/config.py`:
```python
SUPPORTED_FILE_TYPES: str = ".pdf,.docx,.png,.jpg,.jpeg,.tif,.tiff,.bmp"
```

### Environment Variables
No new environment variables required. OCR is automatically enabled when libraries are available.

## Testing

Run OCR tests:
```bash
cd backend
python -m pytest tests/test_ocr.py -v
```

Run all extraction tests:
```bash
python -m pytest tests/test_phase1.py tests/test_ocr.py -v
```

## API Examples

### Upload Scanned PDF
```bash
curl -X POST http://localhost:8000/api/contracts/upload \\
  -H "Authorization: Bearer $TOKEN" \\
  -F "file=@scanned_contract.pdf"
```

Response includes OCR metadata:
```json
{
  "contract_id": "uuid",
  "filename": "scanned_contract.pdf",
  "status": "extracting",
  "metadata": {
    "parser": "pytesseract_ocr",
    "ocr_applied": true
  }
}
```

### Upload Image
```bash
curl -X POST http://localhost:8000/api/contracts/upload \\
  -H "Authorization: Bearer $TOKEN" \\
  -F "file=@contract_scan.jpg"
```

## Troubleshooting

### "Tesseract not found" Error
```bash
# Verify installation
which tesseract
tesseract --version

# macOS: Ensure Homebrew path is in PATH
echo $PATH | grep homebrew

# Linux: Reinstall
sudo apt-get install --reinstall tesseract-ocr
```

### Poor OCR Accuracy
- Increase image DPI in `_parse_pdf_with_ocr` (currently 300)
- Add additional language models: `brew install tesseract-lang`
- Pre-process images (deskew, noise removal) before OCR

### Azure Deployment Issues
- Check App Service logs for Tesseract installation errors
- Verify system write permissions for APT packages
- Consider upgrading to Premium tier for full container support

## Performance Considerations

### OCR Processing Time
- Regular PDF: ~0.1-0.5 seconds
- Scanned PDF with OCR: ~2-5 seconds per page
- Image with OCR: ~1-3 seconds

### Recommendations
- Use background task processing (already implemented)
- Consider adding job queue (Celery/Azure Queue) for high volume
- Cache OCR results in blob storage to avoid re-processing

## Security

### File Size Limits
Current limit (10MB) applies to all file types including images:
```python
MAX_FILE_SIZE_MB: int = 10
```

### Supported Formats
Only whitelisted extensions are accepted:
- PDF: `.pdf`
- DOCX: `.docx`
- Images: `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.bmp`

### Path Traversal Protection
Already implemented in storage service for all file types.

## Future Enhancements

1. **Multi-language Support**: Add Arabic, French, Spanish OCR models
2. **Image Pre-processing**: Deskewing, noise removal, contrast enhancement
3. **Confidence Scores**: Return OCR confidence per word/paragraph
4. **Table Detection**: Enhanced table extraction from scanned documents
5. **Handwriting Recognition**: Support for handwritten contracts
