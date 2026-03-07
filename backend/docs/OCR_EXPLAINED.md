# OCR Support - What It Does

## 📋 What OCR Actually Means Here

OCR (Optical Character Recognition) **converts images to text**. Our implementation handles:

### ✅ What IS Supported:

1. **Scanned PDFs (no text layer)**
   - PDFs that are just images/scans of paper documents
   - Example: You scan a paper contract → PDF with images inside
   - We automatically detect these (< 100 chars/page) and apply OCR
   - Extracts text from the scanned images

2. **Image Files Directly**
   - Upload image files: `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.bmp`
   - Example: Photo of a contract, screenshot, scanned image
   - OCR extracts text from the image

3. **Regular PDFs (with text layer)**
   - Normal PDFs with selectable text
   - No OCR needed - we just extract the text directly (faster)
   - Example: PDF created from Word, digitally signed PDFs

4. **Word/DOCX Files**
   - Normal Word documents with text
   - No OCR needed - we extract text with python-docx
   - DOCX files are text-based by design

### ❌ What Does NOT Need OCR:

- **PDFs that already have text** - We extract text directly (no OCR)
- **Word/DOCX documents** - Already contain text (no OCR)
- **PDFs "with OCR already applied"** - If someone already OCR'd it, it has text, so we just extract that text

## 🔍 How Auto-Detection Works

```python
# When you upload a PDF:
1. First, try to extract text normally (fast)
2. Check: Did we get < 100 characters per page?
3. If YES → This is probably a scanned PDF → Apply OCR
4. If NO → We got enough text → Use the extracted text (no OCR needed)
```

## 💡 Real-World Examples

### Example 1: Scanned Paper Contract (NEEDS OCR)
```
You have a paper contract → Scan it → contract_scan.pdf
→ Upload to system
→ System tries text extraction: Gets 10 chars/page
→ Detects it's a scan → Applies OCR automatically
→ Extracts all text from the scanned images
```

### Example 2: Photo of Contract (NEEDS OCR)
```
You take a phone photo → contract_photo.jpg
→ Upload to system
→ System detects .jpg file → Applies OCR directly
→ Extracts text from the image
```

### Example 3: Digital PDF (NO OCR NEEDED)
```
You create contract in Word → Export to PDF → contract.pdf
→ Upload to system
→ System extracts text: Gets 2000 chars/page
→ No OCR needed → Uses extracted text (faster)
```

### Example 4: Word Document (NO OCR NEEDED)
```
You have contract.docx
→ Upload to system
→ System uses python-docx to extract text
→ No OCR needed → Uses extracted text (faster)
```

## ⚡ Performance Comparison

| Document Type | Processing Method | Speed | Text Quality |
|---------------|------------------|-------|--------------|
| Digital PDF | Direct extraction | ~0.1s | Perfect |
| Scanned PDF | OCR (Tesseract) | ~3-5s per page | Good (95%+) |
| DOCX | Direct extraction | ~0.1s | Perfect |
| Image (JPG/PNG) | OCR (Tesseract) | ~2-3s | Good (95%+) |

## 🎯 Summary

**OCR is for documents without text:**
- ✅ Scanned PDFs (images of documents)
- ✅ Photos of contracts
- ✅ Screenshot images

**No OCR needed for:**
- ✅ Regular PDFs (already have text)
- ✅ Word/DOCX files (already have text)
- ✅ Any document where text can be selected/copied

The system **automatically** decides whether to use OCR or direct text extraction based on what it finds in the document.
