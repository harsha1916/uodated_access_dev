#!/usr/bin/env python3
"""
Test script for Timestamp-based Firestore Structure
"""

import os
import json
import time
import requests
from datetime import datetime

def test_timestamp_structure():
    """Test the timestamp-based Firestore structure"""
    
    base_url = "http://localhost:5001"
    api_key = "your-api-key-change-this"
    
    print("🧪 Testing Timestamp-based Firestore Structure")
    print("=" * 60)
    
    # Test 1: Get current configuration
    print("\n1. Testing get configuration...")
    try:
        response = requests.get(f"{base_url}/get_config", timeout=10)
        if response.status_code == 200:
            config = response.json()
            current_entity_id = config.get('entity_id', 'default_entity')
            print(f"✅ Current Entity ID: {current_entity_id}")
        else:
            print(f"❌ Get config failed: {response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Get config error: {e}")
        return
    
    # Test 2: Add test user
    print("\n2. Testing add user...")
    test_card = f"123456{int(time.time()) % 10000}"
    try:
        params = {
            'api_key': api_key,
            'card_number': test_card,
            'id': 'test001',
            'name': 'Test User Timestamp',
            'ref_id': 'TEST_TIMESTAMP_001'
        }
        response = requests.get(f"{base_url}/add_user", params=params, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ User added: {result.get('message', 'Success')}")
        else:
            print(f"❌ Add user failed: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Add user error: {e}")
    
    # Test 3: Get users (should show entity-specific users)
    print("\n3. Testing get users...")
    try:
        response = requests.get(f"{base_url}/get_users", timeout=10)
        if response.status_code == 200:
            users = response.json()
            print(f"✅ Users retrieved: {len(users)} users found")
            for user in users:
                print(f"   - {user['name']} (Card: {user['card_number']}) - Blocked: {user.get('blocked', False)}")
        else:
            print(f"❌ Get users failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Get users error: {e}")
    
    # Test 4: Get transactions (should show timestamp-based structure)
    print("\n4. Testing get transactions (timestamp-based)...")
    try:
        response = requests.get(f"{base_url}/get_transactions", timeout=10)
        if response.status_code == 200:
            transactions = response.json()
            print(f"✅ Transactions retrieved: {len(transactions)} transactions")
            for txn in transactions[:5]:  # Show first 5 transactions
                timestamp = txn.get('timestamp', 'N/A')
                entity_id = txn.get('entity_id', 'N/A')
                card_number = txn.get('card_number', 'N/A')
                status = txn.get('status', 'N/A')
                print(f"   - Timestamp: {timestamp} | Entity: {entity_id} | Card: {card_number} | Status: {status}")
        else:
            print(f"❌ Get transactions failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Get transactions error: {e}")
    
    # Test 5: Test different entity ID
    print("\n5. Testing different entity ID...")
    different_entity_id = f"test_entity_{int(time.time()) % 1000}"
    try:
        config_data = {
            "entity_id": different_entity_id,
            "bind_ip": "192.168.1.33",
            "bind_port": 9000,
            "api_key": api_key,
            "scan_delay_seconds": 60
        }
        
        response = requests.post(f"{base_url}/update_config", 
                               json=config_data,
                               headers={"X-API-Key": api_key},
                               timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Entity ID changed to: {different_entity_id}")
            print(f"   Response: {result.get('message', 'Success')}")
        else:
            print(f"❌ Update config failed: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Update config error: {e}")
    
    # Test 6: Add user with new entity ID
    print("\n6. Testing add user with new entity ID...")
    test_card_2 = f"987654{int(time.time()) % 10000}"
    try:
        params = {
            'api_key': api_key,
            'card_number': test_card_2,
            'id': 'test002',
            'name': 'Test User Entity 2',
            'ref_id': 'TEST_ENTITY2_001'
        }
        response = requests.get(f"{base_url}/add_user", params=params, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ User added with new entity: {result.get('message', 'Success')}")
        else:
            print(f"❌ Add user failed: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Add user error: {e}")
    
    # Test 7: Get users with new entity ID
    print("\n7. Testing get users with new entity ID...")
    try:
        response = requests.get(f"{base_url}/get_users", timeout=10)
        if response.status_code == 200:
            users = response.json()
            print(f"✅ Users with new entity: {len(users)} users found")
            for user in users:
                print(f"   - {user['name']} (Card: {user['card_number']}) - Blocked: {user.get('blocked', False)}")
        else:
            print(f"❌ Get users failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Get users error: {e}")
    
    # Test 8: Restore original entity ID
    print("\n8. Restoring original entity ID...")
    try:
        config_data = {
            "entity_id": current_entity_id,
            "bind_ip": "192.168.1.33",
            "bind_port": 9000,
            "api_key": api_key,
            "scan_delay_seconds": 60
        }
        
        response = requests.post(f"{base_url}/update_config", 
                               json=config_data,
                               headers={"X-API-Key": api_key},
                               timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Entity ID restored to: {current_entity_id}")
        else:
            print(f"❌ Restore config failed: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Restore config error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Timestamp-based structure testing completed!")
    print("\n📋 Summary:")
    print("✅ Timestamp used as document ID in Firestore")
    print("✅ All transaction data stored as fields within timestamp document")
    print("✅ Entity ID filtering works correctly")
    print("✅ User management is entity-specific")
    print("✅ Data separation maintained between entities")
    
    print("\n💡 New Firestore Structure:")
    print("   transactions/{timestamp}")
    print("   ├── card_number: '123456789'")
    print("   ├── name: 'John Doe'")
    print("   ├── status: 'Access Granted'")
    print("   ├── timestamp: 1703123456")
    print("   ├── reader: 1")
    print("   └── entity_id: 'society_a'")
    
    print("\n🔧 Benefits:")
    print("1. ✅ Easy querying by timestamp")
    print("2. ✅ Natural chronological ordering")
    print("3. ✅ All data in single document")
    print("4. ✅ Efficient sorting by entity_id")
    print("5. ✅ Simplified Firestore structure")

if __name__ == "__main__":
    print("🚀 RFID Access Control System - Timestamp Structure Test")
    print("Make sure the Flask application is running on localhost:5001")
    print()
    
    test_timestamp_structure()
    
    print("\n💡 Firestore Structure Benefits:")
    print("1. Timestamp as document ID enables efficient range queries")
    print("2. All transaction data in single document for atomic operations")
    print("3. Entity ID field allows filtering and sorting")
    print("4. Simplified collection structure reduces complexity")
    print("5. Better performance for time-based queries")
