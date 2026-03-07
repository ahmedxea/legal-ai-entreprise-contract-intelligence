"""
Test script to verify the free AI stack (Ollama + Phi-3 + SQLite + sentence-transformers)
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ollama_service import ollama_service
from app.services.sqlite_service import database_service
from app.agents.extraction_agent import ExtractionAgent
from app.models.schemas import Language


async def test_ollama_chat():
    """Test basic chat completion"""
    print("\n Testing Ollama Chat Completion...")
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is a contract?"}
    ]
    
    response = await ollama_service.chat_completion(messages, temperature=0.3, max_tokens=100)
    print(f" Chat response: {response[:150]}...")
    return True


async def test_structured_extraction():
    """Test structured JSON extraction"""
    print("\n Testing Structured Extraction...")
    
    contract_text = """
    SERVICE AGREEMENT
    
    This Agreement is entered into on January 15, 2026, between:
    
    1. Acme Corp (the "Client"), a company registered in Qatar
    2. Tech Solutions Inc (the "Provider"), a company registered in UAE
    
    The Provider agrees to provide software development services for a total fee of QAR 500,000.
    
    Payment Terms: 50% upfront, 50% upon completion.
    
    Term: This agreement shall commence on February 1, 2026 and continue for 12 months.
    
    Governing Law: This agreement shall be governed by the laws of Qatar.
    """
    
    schema = {
        "parties": ["string"],
        "contract_type": "string",
        "total_value": "number",
        "currency": "string",
        "governing_law": "string"
    }
    
    result = await ollama_service.structured_extraction(
        prompt="Extract key contract information",
        context=contract_text,
        schema=schema
    )
    
    print(f" Extracted data: {result}")
    return bool(result.get("parties"))


async def test_embeddings():
    """Test embedding generation"""
    print("\n Testing Embeddings...")
    
    text = "This is a test contract about software development services."
    embeddings = await ollama_service.get_embeddings(text)
    
    print(f" Embedding dimension: {len(embeddings)}")
    print(f" First 5 values: {embeddings[:5]}")
    return len(embeddings) == 384


async def test_extraction_agent():
    """Test the full extraction agent"""
    print("\n Testing Extraction Agent...")
    
    agent = ExtractionAgent()
    
    contract_text = """
    EMPLOYMENT CONTRACT
    
    This Employment Agreement is made on March 1, 2026, between:
    
    Employer: Qatar Tech Ltd, Commercial Registration No. 12345
    Employee: John Smith, Passport No. ABC123456
    
    Position: Senior Software Engineer
    Salary: QAR 25,000 per month
    
    Start Date: March 15, 2026
    Contract Duration: 2 years (renewable)
    
    Benefits:
    - Annual leave: 30 days
    - Health insurance
    - Housing allowance: QAR 5,000 per month
    
    Termination: Either party may terminate with 60 days notice.
    
    Governing Law: Qatar Labour Law
    Jurisdiction: Courts of Doha, Qatar
    """
    
    extracted = await agent.extract_data(contract_text, Language.ENGLISH)
    
    print(f" Parties found: {len(extracted.get('parties', []))}")
    print(f" Financial terms: {len(extracted.get('financial_terms', []))}")
    print(f" Governing law: {extracted.get('governing_law')}")
    
    return len(extracted.get('parties', [])) > 0


async def test_sqlite_database():
    """Test SQLite database operations"""
    print("\n Testing SQLite Database...")
    
    # Create a test contract
    contract_id = await database_service.create_contract(
        user_id="test_user_123",
        filename="test_contract.pdf",
        blob_url="https://example.com/test.pdf",
        language=Language.ENGLISH,
        industry="Technology"
    )
    
    print(f" Created contract: {contract_id}")
    
    # Retrieve the contract
    contract = await database_service.get_contract(contract_id, "test_user_123")
    print(f" Retrieved contract: {contract['filename']}")
    
    # List contracts
    contracts = await database_service.list_contracts("test_user_123")
    print(f" Total contracts: {len(contracts)}")
    
    # Clean up
    await database_service.delete_contract(contract_id)
    print(f" Deleted test contract")
    
    return True


async def main():
    """Run all tests"""
    print("=" * 70)
    print(" FREE AI STACK TEST SUITE")
    print("=" * 70)
    print("\n Components:")
    print("  - LLM: Microsoft Phi-3 Mini via Ollama")
    print("  - Embeddings: sentence-transformers/all-MiniLM-L6-v2")
    print("  - Database: SQLite")
    print("  - Document Parser: pdfplumber")
    print("=" * 70)
    
    tests = [
        ("Ollama Chat", test_ollama_chat),
        ("Structured Extraction", test_structured_extraction),
        ("Embeddings", test_embeddings),
        ("Extraction Agent", test_extraction_agent),
        ("SQLite Database", test_sqlite_database)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f" {test_name} failed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 70)
    print(" TEST RESULTS")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = " PASS" if result else " FAIL"
        print(f"  {status} - {test_name}")
    
    print(f"\n Score: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n ALL TESTS PASSED! Free AI stack is working perfectly!")
    else:
        print(f"\n️  {total - passed} test(s) failed. Check the output above.")
    
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
