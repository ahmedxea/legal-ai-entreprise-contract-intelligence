"""
Quick test: Run CUAD analysis on one contract and verify entities
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import json
from app.services.cuad_analysis_service import cuad_analysis_service
from app.services.sqlite_service import DatabaseService

async def test_cuad_analysis():
    """Test CUAD analysis on one extracted contract"""
    db = DatabaseService()
    
    # Find one extracted CUAD contract
    conn = db._get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.filename
        FROM contracts c
        INNER JOIN document_text dt ON c.id = dt.document_id
        WHERE c.user_id = 'cuad_test_user'
        AND c.status = 'extracted'
        AND LENGTH(dt.raw_text) > 1000
        LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        print("❌ No extracted CUAD contracts found with text")
        print("Run: cd backend && python scripts/load_cuad_contracts.py")
        return
    
    contract_id = row[0]
    filename = row[1]
    
    print(f"🧪 Testing CUAD Analysis")
    print(f"📄 Contract: {filename}")
    print(f"🆔 ID: {contract_id}\n")
    
    # Run CUAD analysis
    print("⏳ Running analysis... (this may take 30-60 seconds)")
    try:
        result = await cuad_analysis_service.analyze_contract(contract_id)
        
        print("\n✅ Analysis Complete!\n")
        
        # Check extracted entities (18-field schema)
        entities = result.get('extracted_data', {})
        print(f"📊 Entity Extraction (18 fields):")
        print(f"   • Contract Title: {entities.get('contract_title', 'N/A')}")
        print(f"   • Contract Type: {entities.get('contract_type', 'N/A')}")
        print(f"   • Parties: {len(entities.get('parties', []))} found")
        print(f"   • Organizations: {len(entities.get('organizations', []))} found")
        print(f"   • People: {len(entities.get('people', []))} found")
        print(f"   • Addresses: {len(entities.get('addresses', []))} found")
        print(f"   • Effective Date: {entities.get('effective_date', 'N/A')}")
        print(f"   • Expiration Date: {entities.get('expiration_date', 'N/A')}")
        print(f"   • Contract Value: {entities.get('contract_value', 'N/A')}")
        print(f"   • Currency: {entities.get('currency', 'N/A')}")
        print(f"   • Governing Law: {entities.get('governing_law', 'N/A')}")
        print(f"   • Jurisdiction: {entities.get('jurisdiction', 'N/A')}")
        print(f"   • Money Amounts: {len(entities.get('money_amounts', []))} found")
        print(f"   • Percentages: {len(entities.get('percentages', []))} found")
        print(f"   • Obligations: {len(entities.get('obligations', []))} found\n")
        
        # Check risk summary
        risk_summary = result.get('risk_summary', {})
        print(f"⚠️  Risk Assessment:")
        print(f"   • Overall Risk: {risk_summary.get('overall_risk', 'N/A')}")
        print(f"   • High Risk Items: {len(risk_summary.get('high_risk_items', []))}")
        print(f"   • Medium Risk Items: {len(risk_summary.get('medium_risk_items', []))}")
        print(f"   • Risk Flags: {len(risk_summary.get('risk_flags', []))} generated\n")
        
        # Show risk flags
        risk_flags = risk_summary.get('risk_flags', [])
        if risk_flags:
            print(f"🚩 Risk Flags Detected:")
            for i, flag in enumerate(risk_flags[:5], 1):
                print(f"   {i}. {flag}")
            if len(risk_flags) > 5:
                print(f"   ... and {len(risk_flags) - 5} more")
        
        # Check gap analysis
        gap_analysis = result.get('gap_analysis', {})
        print(f"\n📈 Completeness: {gap_analysis.get('completeness_score', 0)}%")
        
        # Verify database storage
        print(f"\n💾 Verifying Database Storage...")
        contract = await db.get_contract_by_id(contract_id)
        
        if contract and contract.get('analysis'):
            analysis_data = contract['analysis']
            print(f"   ✅ Analysis type: {analysis_data.get('analysis_type')}")
            print(f"   ✅ Entities stored: {len(analysis_data.get('entities', {}))} fields")
            print(f"   ✅ Risk flags stored: {len(analysis_data.get('risk_summary', {}).get('risk_flags', []))}")
            
            # Show what frontend will see
            print(f"\n🖥️  Frontend Access Paths:")
            print(f"   • contract.extracted_data.parties = {len(contract.get('extracted_data', {}).get('parties', []))} parties")
            print(f"   • contract.analysis.entities.parties = {len(analysis_data.get('entities', {}).get('parties', []))} parties")
            print(f"   • contract.analysis.entities.governing_law = {analysis_data.get('entities', {}).get('governing_law', 'N/A')}")
            print(f"   • contract.analysis.risk_summary.risk_flags = {len(analysis_data.get('risk_summary', {}).get('risk_flags', []))} flags")
        else:
            print(f"   ❌ Analysis not found in database")
        
        print(f"\n🎉 Test Complete!")
        print(f"\n📝 Next Steps:")
        print(f"   1. Open UI: http://localhost:3000/contracts")
        print(f"   2. Find contract: {filename}")
        print(f"   3. Click 'View Details'")
        print(f"   4. Should see 'Key Details' section with parties, dates, governing law")
        print(f"   5. Should see Risk Flags in analysis results")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_cuad_analysis())
