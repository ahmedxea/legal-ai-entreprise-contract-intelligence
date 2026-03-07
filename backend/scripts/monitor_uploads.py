"""
Real-time upload monitor - watch for new uploads and their processing
"""
import sqlite3
import time
from datetime import datetime

print("🔍 Monitoring uploads in real-time...")
print("=" * 70)
print("Waiting for new uploads... (Press Ctrl+C to stop)\n")

last_count = 0
conn = sqlite3.connect('data/contracts.db')

try:
    while True:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, filename, status, file_size, upload_date 
            FROM contracts 
            ORDER BY upload_date DESC 
            LIMIT 5
        """)
        contracts = cursor.fetchall()
        current_count = len(contracts)
        
        if current_count > last_count or (contracts and contracts[0][2] != 'uploaded'):
            # New upload or status change
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Latest Uploads:")
            print("-" * 70)
            for contract in contracts:
                contract_id, filename, status, file_size, upload_date = contract
                size_kb = file_size / 1024 if file_size else 0
                status_emoji = {
                    'uploaded': '📤',
                    'processing': '⚙️',
                    'extracting': '📄',
                    'extracted': '✅',
                    'analyzed': '🎯',
                    'failed': '❌'
                }.get(status, '❓')
                
                print(f"{status_emoji} {filename[:40]:<40} | {status:<12} | {size_kb:>6.1f} KB")
                print(f"   ID: {contract_id[:8]}... | {upload_date}")
                
            last_count = current_count
        
        time.sleep(2)
        
except KeyboardInterrupt:
    print("\n\n✅ Monitoring stopped")
finally:
    conn.close()
