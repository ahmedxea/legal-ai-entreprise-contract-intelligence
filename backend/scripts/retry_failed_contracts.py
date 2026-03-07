"""
Retry processing for failed contracts
"""
import sys
import asyncio
import sqlite3
sys.path.insert(0, '.')

from app.services.document_processor import DocumentProcessorService


async def main():
    processor = DocumentProcessorService()
    
    try:
        # Connect to database
        conn = sqlite3.connect('data/contracts.db')
        cursor = conn.cursor()
        
        # Get all failed contracts
        cursor.execute("""
            SELECT id, filename, file_type, blob_url 
            FROM contracts 
            WHERE status = 'failed' 
            ORDER BY upload_date DESC
        """)
        
        failed = cursor.fetchall()
        
        if not failed:
            print("✅ No failed contracts found!")
            conn.close()
            return
        
        print(f"📋 Found {len(failed)} failed contracts")
        print("=" * 60)
        
        for row in failed:
            contract_id, filename, file_type, blob_url = row
            
            print(f"\n🔄 Retrying: {filename[:50]}...")
            print(f"   ID: {contract_id}")
            print(f"   Type: {file_type}")
            
            try:
                # Retry processing
                await processor.process(contract_id, blob_url, file_type)
                
                # Check new status
                cursor.execute("SELECT status FROM contracts WHERE id = ?", (contract_id,))
                result = cursor.fetchone()
                new_status = result[0] if result else "unknown"
                
                if new_status == "extracted":
                    print(f"   ✅ SUCCESS! Status: {new_status}")
                else:
                    print(f"   ⚠️  Status: {new_status}")
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:100]}")
        
        print("\n" + "=" * 60)
        
        # Summary
        cursor.execute("SELECT status, COUNT(*) FROM contracts GROUP BY status")
        final_status = cursor.fetchall()
        
        print("\n📊 Final Status Summary:")
        for status, count in final_status:
            print(f"   {status}: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Script error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
