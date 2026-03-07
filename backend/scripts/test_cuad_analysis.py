"""
Test CUAD Analysis on loaded contracts
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.cuad_analysis_service import cuad_analysis_service
from app.services.database_service import DatabaseService


async def test_cuad_analysis():
    """Test CUAD analysis on first loaded contract"""
    
    db = DatabaseService()
    conn = db._get_connection()
    cursor = conn.cursor()
    
    # Get first CUAD contract with EXTRACTED status
    cursor.execute("""
        SELECT id, filename, status FROM contracts 
        WHERE user_id = 'cuad_test_user' AND status = 'EXTRACTED'
        LIMIT 1
    """)
    
    contract = cursor.fetchone()
    conn.close()
    
    if not contract:
        print("❌ No CUAD contracts found with EXTRACTED status")
        print("Run: sqlite3 data/contracts.db \"UPDATE contracts SET status = 'EXTRACTED' WHERE user_id = 'cuad_test_user';\"")
        return
    
    contract_id = contract['id']
    filename = contract['filename']
    status = contract['status']
    
    print("="*70)
    print(f"🧪 Testing CUAD Analysis (15 clause types)")
    print(f"Contract: {filename}")
    print(f"ID: {contract_id}")
    print(f"Status: {status}")
    print("="*70)
    print("\n⏳ Starting analysis (this may take 30-60 seconds)...\n")
    
    try:
        result = await cuad_analysis_service.analyze_contract(contract_id)
        
        if not result:
            print("❌ Analysis failed - no result returned")
            return
        
        print("✅ Analysis completed successfully!\n")
        
        # Display results
        risk_summary = result.get("risk_summary", {})
        clause_analysis = result.get("clause_analysis", {})
        gap_analysis = result.get("gap_analysis", {})
        
        print("📊 RISK SUMMARY")
        print("-" * 70)
        print(f"Overall Risk: {risk_summary.get('overall_risk', 'UNKNOWN')}")
        print(f"High-Risk Items: {len(risk_summary.get('high_risk_items', []))}")
        print(f"Medium-Risk Items: {len(risk_summary.get('medium_risk_items', []))}")
        print(f"Missing Clauses: {len(risk_summary.get('missing_clauses', []))}")
        
        if risk_summary.get('high_risk_items'):
            print("\n⚠️  HIGH RISK ITEMS:")
            for item in risk_summary['high_risk_items'][:3]:
                print(f"   • {item.get('clause')}: {item.get('reason')}")
        
        print("\n📋 CLAUSE COVERAGE")
        print("-" * 70)
        clauses_found = 0
        clauses_total = 15
        
        clause_fields = [
            'governing_law', 'confidentiality', 'termination', 'liability',
            'indemnification', 'payment_terms', 'intellectual_property',
            'data_protection', 'force_majeure', 'non_compete', 'exclusivity',
            'change_of_control', 'anti_assignment', 'audit_rights',
            'post_termination_services'
        ]
        
        for clause_name in clause_fields:
            clause_data = clause_analysis.get(clause_name, {})
            if clause_data.get('present'):
                clauses_found += 1
        
        coverage_pct = (clauses_found / clauses_total) * 100
        print(f"Clauses Found: {clauses_found}/{clauses_total} ({coverage_pct:.1f}%)")
        
        print("\n🔍 GAP ANALYSIS")
        print("-" * 70)
        print(f"Completeness: {gap_analysis.get('completeness_percentage', 0):.1f}%")
        print(f"Assessment: {gap_analysis.get('assessment', 'UNKNOWN')}")
        
        if gap_analysis.get('critical_gaps'):
            print(f"\n🚨 Critical Gaps: {len(gap_analysis['critical_gaps'])}")
            for gap in gap_analysis['critical_gaps'][:3]:
                print(f"   • {gap.get('clause_type')}")
        
        print("\n" + "="*70)
        print("✅ Test completed successfully!")
        print("="*70)
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_cuad_analysis())
