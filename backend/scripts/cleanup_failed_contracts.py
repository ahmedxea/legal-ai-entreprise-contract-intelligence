"""
Clean up failed contracts that have missing files
"""
import sys
import sqlite3
sys.path.insert(0, '.')


def main():
    conn = sqlite3.connect('data/contracts.db')
    cursor = conn.cursor()
    
    # Get failed contracts
    cursor.execute("""
        SELECT id, filename, blob_url 
        FROM contracts 
        WHERE status = 'failed'
    """)
    
    failed = cursor.fetchall()
    
    if not failed:
        print("✅ No failed contracts to clean up")
        return
    
    print(f"📋 Found {len(failed)} failed contracts")
    print("\nFailed Contracts:")
    print("=" * 80)
    
    for contract_id, filename, blob_url in failed:
        print(f"- {filename[:60]}")
        print(f"  ID: {contract_id}")
        print(f"  Path: {blob_url}")
        print()
    
    print("\nThese contracts have missing files and cannot be recovered.")
    print("\n⚠️  Options:")
    print("   1. Delete these records (clean database)")
    print("   2. Keep them (for reference)")
    print("   3. Re-upload the original files")
    
    response = input("\nDelete failed contracts? (yes/no): ").strip().lower()
    
    if response == 'yes':
        cursor.execute("DELETE FROM contracts WHERE status = 'failed'")
        conn.commit()
        deleted = cursor.rowcount
        print(f"\n✅ Deleted {deleted} failed contract records")
    else:
        print("\n📌 Keeping failed contracts in database")
    
    conn.close()


if __name__ == "__main__":
    main()
