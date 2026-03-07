"""
Test entity extraction in CUAD analysis
"""
import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.database_service import DatabaseService


async def test_entity_extraction():
    """Test that entities are now being extracted"""
    
    db = DatabaseService()
    conn = db._get_connection()
    cursor = conn.cursor()
    
    # Get a CUAD contract that's already analyzed
    cursor.execute("""
        SELECT id, filename, extracted_data, analysis
        FROM contracts 
        WHERE user_id = 'cuad_test_user' 
        LIMIT 1
    """)
    
    contract = cursor.fetchone()
    conn.close()
    
    if not contract:
        print("❌ No CUAD contracts found")
        return
    
    contract_id = contract['id']
    filename = contract['filename']
    extracted_data_raw = contract['extracted_data']
    analysis_raw = contract['analysis']
    
    print("="*70)
    print(f"📋 Contract: {filename}")
    print(f"   ID: {contract_id}")
    print("="*70)
    
    # Check extracted_data column
    print("\n🔍 EXTRACTED_DATA COLUMN:")
    print("-" * 70)
    if extracted_data_raw:
        try:
            extracted_data = json.loads(extracted_data_raw) if isinstance(extracted_data_raw, str) else extracted_data_raw
            
            parties = extracted_data.get('parties', [])
            print(f"✅ Parties: {len(parties)} found")
            if parties:
                for i, party in enumerate(parties[:3], 1):
                    print(f"   {i}. {party.get('name', 'Unknown')} ({party.get('role', 'N/A')})")
            
            key_dates = extracted_data.get('key_dates', [])
            print(f"✅ Key Dates: {len(key_dates)} found")
            if key_dates:
                for i, date in enumerate(key_dates[:3], 1):
                    print(f"   {i}. {date.get('date_type', 'Unknown')}: {date.get('date', 'N/A')}")
            
            governing_law = extracted_data.get('governing_law')
            print(f"✅ Governing Law: {governing_law or 'Not found'}")
            
            contract_type = extracted_data.get('contract_type')
            print(f"✅ Contract Type: {contract_type or 'Not found'}")
            
        except Exception as e:
            print(f"❌ Error parsing extracted_data: {e}")
    else:
        print("⚠️  extracted_data column is empty")
    
    # Check analysis column for entities
    print("\n🔍 ANALYSIS COLUMN (entities):")
    print("-" * 70)
    if analysis_raw:
        try:
            analysis = json.loads(analysis_raw) if isinstance(analysis_raw, str) else analysis_raw
            entities = analysis.get('entities', {})
            
            if entities:
                print(f"✅ Entities found in analysis")
                parties = entities.get('parties', [])
                print(f"   Parties: {len(parties)}")
                print(f"   Governing Law: {entities.get('governing_law', 'N/A')}")
                print(f"   Contract Type: {entities.get('contract_type', 'N/A')}")
            else:
                print("⚠️  No entities section in analysis")
                
        except Exception as e:
            print(f"❌ Error parsing analysis: {e}")
    else:
        print("⚠️  analysis column is empty")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(test_entity_extraction())
