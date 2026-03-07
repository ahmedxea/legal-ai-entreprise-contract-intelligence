"""
Load CUAD contracts into Lexra database for testing

This script:
1. Loads contracts from the CUAD dataset
2. Inserts them into Lexra's SQLite database
3. Marks them as "extracted" so they're ready for CUAD analysis
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.storage_factory import storage
from app.services.sqlite_service import DatabaseService
from app.models.schemas import ContractStatus, Language


async def load_cuad_contracts(num_contracts: int = 15, start_idx: int = 0):
    """
    Load CUAD contracts into Lexra database
    
    Args:
        num_contracts: Number of contracts to load (default: 15)
        start_idx: Starting index in CUAD dataset (default: 0)
    """
    
    # Load CUAD dataset
    cuad_path = Path(__file__).parent.parent.parent / "cuad-main" / "data" / "CUADv1.json"
    
    if not cuad_path.exists():
        print(f"❌ CUAD dataset not found at: {cuad_path}")
        print("Please ensure cuad-main/data/CUADv1.json exists")
        return
    
    print(f"📖 Loading CUAD dataset from: {cuad_path}")
    with open(cuad_path, 'r', encoding='utf-8') as f:
        cuad_data = json.load(f)
    
    total_available = len(cuad_data["data"])
    print(f"✓ Found {total_available} contracts in CUAD dataset")
    
    # Validate indices
    if start_idx >= total_available:
        print(f"❌ Start index {start_idx} exceeds dataset size {total_available}")
        return
    
    end_idx = min(start_idx + num_contracts, total_available)
    actual_num = end_idx - start_idx
    
    print(f"📦 Will load contracts {start_idx} to {end_idx-1} ({actual_num} total)")
    
    # Initialize database
    db = DatabaseService()
    
    loaded_count = 0
    skipped_count = 0
    
    # Process contracts
    for idx in range(start_idx, end_idx):
        contract_data = cuad_data["data"][idx]
        title = contract_data["title"]
        
        # Extract contract text (stored in the first paragraph's context)
        if not contract_data.get("paragraphs") or len(contract_data["paragraphs"]) == 0:
            print(f"⚠️  Skipping {title}: no paragraphs found")
            skipped_count += 1
            continue
        
        contract_text = contract_data["paragraphs"][0]["context"]
        text_length = len(contract_text)
        
        # Create a clean filename/identifier
        contract_id = f"cuad_{idx:03d}_{title[:50]}"
        contract_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in contract_id)
        
        try:
            # Create a simple blob_url for reference
            blob_url = f"cuad_contracts/{contract_id}.txt"
            
            # Create contract in database using the standard method
            new_contract_id = await db.create_contract(
                user_id="cuad_test_user",
                filename=f"{title[:100]}.txt",
                blob_url=blob_url,
                language=Language.ENGLISH,
                industry="General Commercial",
                file_size=text_length,
                file_type="text/plain"
            )
            
            # Save the document text separately
            paragraphs = contract_text.split('\n\n')  # Simple paragraph splitting
            await db.save_document_text(
                document_id=new_contract_id,
                raw_text=contract_text,
                paragraphs=paragraphs,
                page_count=None,
                file_type="text/plain"
            )
            
            # Update status to EXTRACTED and add metadata
            conn = db._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE contracts 
                SET status = ?,
                    extracted_data = ?
                WHERE id = ?
            """, (
                ContractStatus.EXTRACTED.value,
                json.dumps({
                    "source": "CUAD",
                    "cuad_index": idx,
                    "original_title": title,
                    "text_length": text_length
                }),
                new_contract_id
            ))
            conn.commit()
            conn.close()
            
            contract_id = new_contract_id
            
            loaded_count += 1
            print(f"✓ [{loaded_count}/{actual_num}] Loaded: {title[:60]}... ({text_length:,} chars)")
            
        except Exception as e:
            print(f"❌ Error loading {title}: {e}")
            skipped_count += 1
            continue
    
    print("\n" + "="*70)
    print(f"📊 Summary:")
    print(f"   Successfully loaded: {loaded_count} contracts")
    print(f"   Skipped/Failed: {skipped_count} contracts")
    print(f"   User ID: cuad_test_user")
    print(f"   Status: EXTRACTED (ready for CUAD analysis)")
    print("="*70)
    
    # Display sample contract IDs for testing
    if loaded_count > 0:
        print("\n🧪 Sample contract IDs for testing:")
        conn = db._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM contracts 
            WHERE user_id = 'cuad_test_user' 
            ORDER BY upload_date DESC 
            LIMIT 3
        """)
        sample_contracts = cursor.fetchall()
        conn.close()
        
        for i, contract in enumerate(sample_contracts, 1):
            print(f"   {i}. {contract['id']}")
        print("\n💡 Test CUAD analysis with:")
        print(f"   curl -X POST http://localhost:8000/api/contracts/<contract_id>/cuad-analysis \\")
        print(f"        -H 'Authorization: Bearer test_token'")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Load CUAD contracts into Lexra")
    parser.add_argument("--num", type=int, default=15, help="Number of contracts to load (default: 15)")
    parser.add_argument("--start", type=int, default=0, help="Starting index in CUAD dataset (default: 0)")
    
    args = parser.parse_args()
    
    asyncio.run(load_cuad_contracts(num_contracts=args.num, start_idx=args.start))
