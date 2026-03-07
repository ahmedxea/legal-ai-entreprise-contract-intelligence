"""
Re-run CUAD analysis with entity extraction
"""
import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.cuad_analysis_service import cuad_analysis_service


async def reanalyze_contract():
    """Re-run CUAD analysis to test entity extraction"""
    
    contract_id = "d4972440-7953-4132-ad07-ee388337937e"
    
    print("="*70)
    print("🔄 Re-running CUAD Analysis with Entity Extraction")
    print(f"Contract ID: {contract_id}")
    print("="*70)
    print("\n⏳ Starting analysis (this may take 60-90 seconds)...\n")
    
    try:
        result = await cuad_analysis_service.analyze_contract(contract_id)
        
        if not result:
            print("❌ Analysis failed - no result returned")
            return
        
        print("✅ Analysis completed successfully!\n")
        
        # Display entity extraction results
        extracted_data = result.get("extracted_data", {})
        
        print("📋 EXTRACTED ENTITIES")
        print("-" * 70)
        
        parties = extracted_data.get('parties', [])
        print(f"Parties: {len(parties)}")
        if parties:
            for i, party in enumerate(parties[:3], 1):
                name = party.get('name', 'Unknown')
                role = party.get('role', 'N/A')
                print(f"  {i}. {name} ({role})")
        
        key_dates = extracted_data.get('key_dates', [])
        print(f"\nKey Dates: {len(key_dates)}")
        if key_dates:
            for i, date in enumerate(key_dates[:3], 1):
                date_type = date.get('date_type', 'Unknown')
                date_val = date.get('date', 'N/A')
                print(f"  {i}. {date_type}: {date_val}")
        
        governing_law = extracted_data.get('governing_law')
        print(f"\nGoverning Law: {governing_law or 'Not found'}")
        
        contract_type = extracted_data.get('contract_type')
        print(f"Contract Type: {contract_type or 'Not found'}")
        
        financial_terms = extracted_data.get('financial_terms', [])
        print(f"Financial Terms: {len(financial_terms)}")
        
        # Display clause analysis summary
        clause_analysis = result.get("clause_analysis", {})
        risk_summary = result.get("risk_summary", {})
        
        print("\n📊 CLAUSE ANALYSIS")
        print("-" * 70)
        print(f"Overall Risk: {risk_summary.get('overall_risk', 'UNKNOWN')}")
        print(f"Completeness: {result.get('completeness_score', 0)}%")
        
        print("\n" + "="*70)
        print("✅ Test completed successfully!")
        print("="*70)
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(reanalyze_contract())
