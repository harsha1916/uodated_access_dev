#!/usr/bin/env python3
"""
Test script to verify increased transaction limit on dashboard
"""

import requests
import json

def test_transaction_limit():
    """Test that the dashboard now shows more than 10 transactions"""
    
    base_url = "http://localhost:5001"
    
    print("🧪 Testing Transaction Limit Increase")
    print("=" * 50)
    
    try:
        # Test get_transactions endpoint
        print("\n1. Testing get_transactions endpoint...")
        response = requests.get(f"{base_url}/get_transactions", timeout=10)
        
        if response.status_code == 200:
            transactions = response.json()
            transaction_count = len(transactions)
            
            print(f"✅ Transactions retrieved: {transaction_count}")
            
            if transaction_count > 10:
                print(f"🎉 SUCCESS: Dashboard now shows {transaction_count} transactions (more than 10)")
            elif transaction_count == 10:
                print("⚠️  WARNING: Still showing only 10 transactions")
            else:
                print(f"ℹ️  INFO: Showing {transaction_count} transactions (less than 10 available)")
            
            # Show first few transactions
            print(f"\n📋 First 5 transactions:")
            for i, txn in enumerate(transactions[:5]):
                timestamp = txn.get('timestamp', 'N/A')
                card_number = txn.get('card_number', 'N/A')
                name = txn.get('name', 'N/A')
                status = txn.get('status', 'N/A')
                entity_id = txn.get('entity_id', 'N/A')
                print(f"   {i+1}. Card: {card_number} | Name: {name} | Status: {status} | Entity: {entity_id}")
            
            # Show last few transactions
            if transaction_count > 5:
                print(f"\n📋 Last 5 transactions:")
                for i, txn in enumerate(transactions[-5:]):
                    timestamp = txn.get('timestamp', 'N/A')
                    card_number = txn.get('card_number', 'N/A')
                    name = txn.get('name', 'N/A')
                    status = txn.get('status', 'N/A')
                    entity_id = txn.get('entity_id', 'N/A')
                    print(f"   {transaction_count-4+i}. Card: {card_number} | Name: {name} | Status: {status} | Entity: {entity_id}")
            
        else:
            print(f"❌ Failed to get transactions: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🔧 Changes Made:")
    print("✅ Increased Firestore query limit from 100 to 200")
    print("✅ Increased display limit from 10 to 50 transactions")
    print("✅ Increased offline cache limit from 10 to 50 transactions")
    
    print("\n💡 Benefits:")
    print("1. Dashboard now shows up to 50 transactions")
    print("2. Better historical view of access events")
    print("3. More data for analysis and monitoring")
    print("4. Improved user experience with more context")

if __name__ == "__main__":
    print("🚀 RFID Access Control System - Transaction Limit Test")
    print("Make sure the Flask application is running on localhost:5001")
    print()
    
    test_transaction_limit()
    
    print("\n📝 Note:")
    print("- If you have fewer than 50 transactions in your system, you'll see all available")
    print("- The limit ensures good performance while showing more data")
    print("- You can further increase the limit by modifying the code if needed")
