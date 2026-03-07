"""
Tests for OCR functionality
"""
import pytest
import io
from PIL import Image, ImageDraw, ImageFont
from app.agents.document_parser import DocumentParserAgent


class TestOCR:
    """Test OCR capabilities for scanned documents and images"""
    
    @pytest.mark.asyncio
    async def test_can_import_ocr_libraries(self):
        """Verify OCR libraries are available"""
        try:
            import pytesseract
            from pdf2image import convert_from_bytes
            from PIL import Image
            assert True
        except ImportError as e:
            pytest.fail(f"OCR libraries not available: {e}")
    
    @pytest.mark.asyncio
    async def test_parse_text_image(self):
        """Test OCR on a simple text image"""
        agent = DocumentParserAgent()
        
        # Create a simple test image with text
        img = Image.new('RGB', (800, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw some text (using default font)
        text = "THIS IS A CONTRACT TEST"
        draw.text((50, 80), text, fill='black')
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Parse the image
        result = await agent._parse_image(img_bytes.read(), "test.png")
        
        # Verify structure
        assert result is not None
        assert 'full_text' in result
        assert 'pages' in result
        assert 'file_type' in result
        assert result['file_type'] == 'image'
        assert result['page_count'] == 1
        
        # OCR should extract some text (may not be perfect)
        extracted_text = result['full_text'].upper()
        assert len(extracted_text) > 0
        assert 'metadata' in result
        assert result['metadata'].get('ocr_applied') is True
    
    @pytest.mark.asyncio
    async def test_ocr_metadata(self):
        """Test that OCR adds proper metadata"""
        agent = DocumentParserAgent()
        
        # Create test image
        img = Image.new('RGB', (400, 100), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((20, 40), "SCANNED DOCUMENT", fill='black')
        
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        result = await agent._parse_image(img_bytes.read(), "scan.jpg")
        
        # Check metadata
        assert result['metadata']['parser'] == 'pytesseract_ocr'
        assert result['metadata']['ocr_applied'] is True
        assert 'image_format' in result['metadata']
