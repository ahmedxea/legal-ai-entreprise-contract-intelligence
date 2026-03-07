"""Simple CUAD analysis test"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
from app.services.cuad_analysis_service import cuad_analysis_service

async def main():
    contract_id = '71d3cc66-48c7-43f4-bef3-e2f9f42e2302'
    
    print('🚀 Starting CUAD Analysis...')
    print('📄 Contract: ADAMSGOLFINC Endorsement Agreement')
    print('⏳ Processing (30-60 seconds)...\n')
    
    result = await cuad_analysis_service.analyze_contract(contract_id)
    
    entities = result['extracted_data']
    risks = result['risk_summary']['risk_flags']
    
    print('\n✅ Analysis Complete!')
    print('\n📊 Entity Extraction Results:')
    print(f'   • Parties: {len(entities.get("parties", []))}')
    print(f'   • Organizations: {len(entities.get("organizations", []))}')
    print(f'   • Governing Law: {entities.get("governing_law", "N/A")}')
    print(f'   • Effective Date: {entities.get("effective_date", "N/A")}')
    print(f'   • Contract Value: {entities.get("contract_value", "N/A")}')
    
    print('\n⚠️  Risk Assessment:')
    print(f'   • Overall Risk: {result["overall_risk"]}')
    print(f'   • Risk Flags: {len(risks)}')
    
    if risks:
        print('\n🚩 Risk Flags Detected:')
        for i, flag in enumerate(risks[:5], 1):
            print(f'   {i}. {flag}')
        if len(risks) > 5:
            print(f'   ... and {len(risks) - 5} more')
    
    print(f'\n📈 Completeness: {result["completeness_score"]}%')
    print(f'\n✨ Contract ID: {contract_id}')
    print(f'🌐 View in UI: http://localhost:3000/contracts/detail?id={contract_id}')
    print('\n🎉 The "Key Details" section should now show parties, dates, and governing law!')

if __name__ == "__main__":
    asyncio.run(main())
