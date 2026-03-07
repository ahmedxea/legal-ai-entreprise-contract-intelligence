"""Quick test of entity extraction in CUAD analysis"""
import asyncio
import json
from app.services.cuad_analysis_service import cuad_analysis_service

async def quick_test():
    contract_id = "2bf02218-2233-421b-96c8-0d3f528521dd"
    
    print("🧪 Testing Entity Extraction in CUAD Analysis")
    print(f"Contract: {contract_id}")
    print("⏳ Running analysis...\n")
    
    try:
        result = await cuad_analysis_service.analyze_contract(contract_id)
        
        # Check extracted entities
        extracted = result.get("extracted_data", {})
        print("✅ Analysis Complete!\n")
        print("📋 EXTRACTED ENTITIES:")
        print(f"   Parties: {len(extracted.get('parties', []))}")
        print(f"   Key Dates: {len(extracted.get('key_dates', []))}")
        print(f"   Governing Law: {extracted.get('governing_law', 'Not found')}")
        print(f"   Contract Type: {extracted.get('contract_type', 'Not found')}")
        
        if extracted.get('parties'):
            print("\n   Sample Party:")
            party = extracted['parties'][0]
            print(f"   • {party.get('name', 'N/A')} ({party.get('role', 'N/A')})")
        
        print(f"\n📊 Risk: {result.get('overall_risk', 'N/A')}")
        print(f"📈 Completeness: {result.get('completeness_score', 0)}%")
        
    except Exception as e:
        print(f"❌ Error: {e}")

asyncio.run(quick_test())
