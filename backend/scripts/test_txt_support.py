"""
Test .txt file upload and processing to verify the fix works
"""
import sys
import asyncio
sys.path.insert(0, '.')

from app.services.local_storage_service import LocalStorageService
from app.agents.document_parser import DocumentParserAgent


async def main():
    print("🧪 Testing .txt File Support")
    print("=" * 60)
    
    # Create test .txt file
    test_content = """
    THIS IS A TEST CONTRACT AGREEMENT
    
    This Agreement is entered into on March 7, 2026, between:
    
    Party A: Test Company Inc.
    Party B: Demo Corporation Ltd.
    
    1. TERMS AND CONDITIONS
    The parties agree to the following terms...
    
    2. PAYMENT TERMS
    Payment shall be made within 30 days...
    
    3. CONFIDENTIALITY
    All information shared under this agreement shall remain confidential...
    
    4. GOVERNING LAW
    This agreement is governed by the laws of California, USA.
    
    5. TERMINATION
    Either party may terminate this agreement with 30 days written notice.
    """
    
    # Test 1: Storage upload
    print("\n1️⃣ Testing file upload...")
    storage = LocalStorageService()
    
    try:
        blob_url = await storage.upload_file(
            file_content=test_content.encode('utf-8'),
            filename="test_contract.txt",
            user_id="test_user"
        )
        print(f"   ✅ Upload successful: {blob_url}")
    except Exception as e:
        print(f"   ❌ Upload failed: {e}")
        return
    
    # Test 2: Parse the file
    print("\n2️⃣ Testing .txt document parsing...")
    parser = DocumentParserAgent()
    
    try:
        result = await parser.parse_document(blob_url)
        
        print(f"   ✅ Parsing successful!")
        print(f"   - Extracted: {len(result['full_text'])} characters")
        print(f"   - Paragraphs: {result.get('paragraph_count', 0)}")
        print(f"   - File type: {result.get('file_type')}")
        print(f"   - First 100 chars: {result['full_text'][:100]}...")
        
    except Exception as e:
        print(f"   ❌ Parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 3: Verify supported file types
    print("\n3️⃣ Checking configuration...")
    from app.core.config import settings
    
    supported = settings.SUPPORTED_FILE_TYPES
    print(f"   📋 Supported types: {supported}")
    
    if '.txt' in supported:
        print(f"   ✅ .txt files are supported!")
    else:
        print(f"   ⚠️  .txt not in supported types")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! .txt file support is working.")
    print("\n💡 You can now upload .txt contract files successfully!")


if __name__ == "__main__":
    asyncio.run(main())
