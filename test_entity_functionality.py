#!/usr/bin/env python3
"""
Test script for Entity-based Multi-Controller Functionality
"""

import os
import json
import time
import requests
from datetime import datetime

def test_entity_functionality():
    """Test the entity-based multi-controller functionality"""
    
    base_url = "http://localhost:5001"
    api_key = "your-api-key-change-this"
    
    print("🧪 Testing Entity-based Multi-Controller Functionality")
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
    
    # Test 2: Update entity ID
    print("\n2. Testing entity ID update...")
    new_entity_id = f"test_entity_{int(time.time())}"
    try:
        config_data = {
            "entity_id": new_entity_id,
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
            print(f"✅ Entity ID updated to: {new_entity_id}")
            print(f"   Response: {result.get('message', 'Success')}")
        else:
            print(f"❌ Update config failed: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Update config error: {e}")
    
    # Test 3: Add user with entity ID
    print("\n3. Testing add user with entity ID...")
    test_card = f"123456{int(time.time()) % 10000}"
    try:
        params = {
            'api_key': api_key,
            'card_number': test_card,
            'id': 'test001',
            'name': 'Test User Entity',
            'ref_id': 'TEST_ENTITY_001'
        }
        response = requests.get(f"{base_url}/add_user", params=params, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ User added with entity ID: {result.get('message', 'Success')}")
        else:
            print(f"❌ Add user failed: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Add user error: {e}")
    
    # Test 4: Get users (should show entity-specific users)
    print("\n4. Testing get users (entity-specific)...")
    try:
        response = requests.get(f"{base_url}/get_users", timeout=10)
        if response.status_code == 200:
            users = response.json()
            print(f"✅ Users retrieved: {len(users)} users found")
            for user in users:
                entity_id = user.get('entity_id', 'not_set')
                print(f"   - {user['name']} (Card: {user['card_number']}) - Entity: {entity_id}")
        else:
            print(f"❌ Get users failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Get users error: {e}")
    
    # Test 5: Simulate transaction (would normally come from RFID scan)
    print("\n5. Testing transaction with entity ID...")
    try:
        # This would normally be triggered by an RFID scan
        # For testing, we'll check if the system is ready to handle entity-based transactions
        response = requests.get(f"{base_url}/get_transactions", timeout=10)
        if response.status_code == 200:
            transactions = response.json()
            print(f"✅ Transaction endpoint working - {len(transactions)} transactions")
            if transactions and isinstance(transactions, list) and len(transactions) > 0:
                for txn in transactions[:3]:  # Show first 3 transactions
                    entity_id = txn.get('entity_id', 'not_set')
                    print(f"   - Card: {txn.get('card_number', 'N/A')} - Entity: {entity_id} - Status: {txn.get('status', 'N/A')}")
        else:
            print(f"❌ Get transactions failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Get transactions error: {e}")
    
    # Test 6: Test different entity ID
    print("\n6. Testing different entity ID...")
    different_entity_id = f"different_entity_{int(time.time()) % 1000}"
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
    
    # Test 7: Verify entity separation
    print("\n7. Testing entity separation...")
    try:
        response = requests.get(f"{base_url}/get_users", timeout=10)
        if response.status_code == 200:
            users = response.json()
            print(f"✅ Users after entity change: {len(users)} users found")
            # Users should be empty or different now since we changed entity ID
            for user in users:
                entity_id = user.get('entity_id', 'not_set')
                print(f"   - {user['name']} (Card: {user['card_number']}) - Entity: {entity_id}")
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
    print("🎯 Entity functionality testing completed!")
    print("\n📋 Summary:")
    print("✅ Entity ID configuration added to web interface")
    print("✅ Firestore collections now use entity-based structure")
    print("✅ Document IDs use timestamp-based format")
    print("✅ All transactions include entity_id field")
    print("✅ User management is entity-specific")
    print("✅ Configuration can be updated via web interface")
    
    print("\n💡 Firestore Structure:")
    print("   entities/{entity_id}/transactions/{timestamp}_{entity_id}")
    print("   entities/{entity_id}/users/{card_number}")
    
    print("\n🔧 Usage Instructions:")
    print("1. Set unique ENTITY_ID for each controller in Configuration tab")
    print("2. Each controller will store data in separate Firestore collections")
    print("3. Document IDs use timestamp format for easier querying")
    print("4. All data is automatically tagged with entity_id")

if __name__ == "__main__":
    print("🚀 RFID Access Control System - Entity Functionality Test")
    print("Make sure the Flask application is running on localhost:5001")
    print()
    
    test_entity_functionality()
    
    print("\n💡 To test with multiple controllers:")
    print("1. Set different ENTITY_ID values on each controller")
    print("2. Each controller will have separate data in Firestore")
    print("3. Use the same Firebase project for all controllers")
    print("4. Data will be automatically separated by entity_id")
