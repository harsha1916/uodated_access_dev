# Entity-Based Multi-Controller System

## 🏢 **Overview**

The RFID Access Control System now supports **multi-controller deployment** using a single Firestore database. Each controller is identified by a unique **Entity ID**, ensuring complete data separation while sharing the same cloud infrastructure.

## 🎯 **Key Features**

### **✅ Entity-Based Data Separation**
- **Unique Entity ID** for each controller/society
- **Separate Firestore Collections** per entity
- **Isolated User Management** per entity
- **Independent Transaction Logs** per entity

### **✅ Timestamp-Based Document IDs**
- **Predictable Document IDs** using timestamp format
- **Easier Querying** and data retrieval
- **Chronological Ordering** by default
- **No Random ID Conflicts**

### **✅ Web Interface Configuration**
- **Entity ID Field** in Configuration tab
- **Real-time Updates** via web interface
- **Validation** and error handling
- **Persistent Storage** in .env file

## 🏗️ **Firestore Structure**

### **Before (Single Controller)**
```
transactions/
├── random_id_1
├── random_id_2
└── random_id_3

users/
├── card_123456789
├── card_987654321
└── card_555666777
```

### **After (Multi-Controller with Timestamp Structure)**
```
transactions/
├── 1703123456
│   ├── card_number: "123456789"
│   ├── name: "John Doe"
│   ├── status: "Access Granted"
│   ├── timestamp: 1703123456
│   ├── reader: 1
│   └── entity_id: "society_a"
├── 1703123457
│   ├── card_number: "987654321"
│   ├── name: "Jane Smith"
│   ├── status: "Access Denied"
│   ├── timestamp: 1703123457
│   ├── reader: 2
│   └── entity_id: "society_b"
└── 1703123458
    ├── card_number: "555666777"
    ├── name: "Bob Johnson"
    ├── status: "Access Granted"
    ├── timestamp: 1703123458
    ├── reader: 1
    └── entity_id: "society_a"

users/
├── 123456789
│   ├── id: "EMP001"
│   ├── name: "John Doe"
│   ├── ref_id: "REF001"
│   ├── card_number: "123456789"
│   └── entity_id: "society_a"
├── 987654321
│   ├── id: "EMP002"
│   ├── name: "Jane Smith"
│   ├── ref_id: "REF002"
│   ├── card_number: "987654321"
│   └── entity_id: "society_b"
└── 555666777
    ├── id: "EMP003"
    ├── name: "Bob Johnson"
    ├── ref_id: "REF003"
    ├── card_number: "555666777"
    └── entity_id: "society_a"
```

## ⚙️ **Configuration**

### **1. Entity ID Setup**
```bash
# In .env file
ENTITY_ID=society_a
```

### **2. Web Interface Configuration**
1. **Login** to the web interface
2. **Navigate** to Configuration tab
3. **Set Entity ID** in System Configuration section
4. **Click Save** to apply changes
5. **Restart** the system for full effect

### **3. Multiple Controllers Setup**
```bash
# Controller 1 (Society A)
ENTITY_ID=society_a

# Controller 2 (Society B)  
ENTITY_ID=society_b

# Controller 3 (Office Building)
ENTITY_ID=office_building
```

## 📊 **Data Structure**

### **Transaction Document**
```json
{
  "card_number": "123456789",
  "name": "John Doe",
  "status": "Access Granted",
  "timestamp": 1703123456,
  "reader": 1,
  "entity_id": "society_a"
}
```

### **User Document**
```json
{
  "id": "EMP001",
  "ref_id": "REF001",
  "name": "John Doe",
  "card_number": "123456789",
  "entity_id": "society_a"
}
```

## 🔧 **Implementation Details**

### **Document ID Format**
```
{timestamp}
```
- **timestamp**: Unix timestamp of the transaction (used as document ID)

### **Collection Paths**
```
transactions/{timestamp}
users/{card_number}
```

### **Data Structure**
All transaction data is stored as fields within the timestamp document:
- **card_number**: RFID card number
- **name**: User name
- **status**: Access status (Granted/Denied/Blocked)
- **timestamp**: Unix timestamp
- **reader**: Reader ID (1 or 2)
- **entity_id**: Entity identifier for filtering

### **Code Changes Made**

#### **1. Configuration Updates**
```python
# Added entity ID to configuration
ENTITY_ID = os.environ.get('ENTITY_ID', 'default_entity')

# Updated get_config endpoint
config = {
    "entity_id": os.getenv("ENTITY_ID", "default_entity"),
    # ... other config
}
```

#### **2. Firestore Operations**
```python
# Before
db.collection("transactions").add(transaction)

# After
timestamp = transaction.get("timestamp", int(time.time()))
db.collection("transactions").document(str(timestamp)).set(transaction)
```

#### **3. Transaction Structure**
```python
# Added entity_id to all transactions
transaction = {
    "card_number": str(card_int),
    "name": name,
    "status": status,
    "timestamp": timestamp,
    "reader": reader_id,
    "entity_id": ENTITY_ID  # New field
}
```

## 🚀 **Deployment Guide**

### **Single Controller (Existing)**
1. **No changes required** - uses default entity ID
2. **Data migrates** to new structure automatically
3. **Backward compatible** with existing data

### **Multiple Controllers (New)**
1. **Set unique Entity ID** for each controller
2. **Use same Firebase project** for all controllers
3. **Data automatically separated** by entity ID
4. **Independent operation** of each controller

### **Migration from Single to Multi**
1. **Backup existing data** from Firestore
2. **Set Entity ID** on existing controller
3. **Data automatically moves** to entity-based structure
4. **Add new controllers** with different Entity IDs

## 📈 **Benefits**

### **✅ Scalability**
- **Unlimited controllers** in single Firestore project
- **Cost-effective** cloud storage
- **Centralized management** with data separation

### **✅ Data Integrity**
- **Complete isolation** between entities
- **No data conflicts** between controllers
- **Independent user management** per entity

### **✅ Query Performance**
- **Timestamp-based document IDs** for efficient range queries
- **Single collection** with entity filtering for faster access
- **Natural chronological ordering** by document ID
- **Atomic operations** with all data in single document

### **✅ Management**
- **Single Firebase project** for all controllers
- **Centralized monitoring** and analytics
- **Unified backup** and disaster recovery

## 🔍 **Testing**

### **Test Script**
```bash
python3 test_entity_functionality.py
```

### **Manual Testing**
1. **Set different Entity IDs** on multiple controllers
2. **Add users** on each controller
3. **Verify data separation** in Firestore
4. **Test transactions** are entity-specific

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **Issue: Data not separating by entity**
- **Check**: Entity ID is set correctly in .env file
- **Check**: Configuration was saved via web interface
- **Solution**: Restart the system after configuration changes

#### **Issue: Users not showing up**
- **Check**: Entity ID matches between controllers
- **Check**: Firestore permissions are correct
- **Solution**: Verify entity ID in user data

#### **Issue: Transactions in wrong collection**
- **Check**: ENTITY_ID environment variable
- **Check**: Transaction includes entity_id field
- **Solution**: Restart system and verify configuration

### **Debug Commands**
```bash
# Check current entity ID
curl http://localhost:5001/get_config | jq '.entity_id'

# Check users with entity ID
curl http://localhost:5001/get_users | jq '.[].entity_id'

# Check transactions with entity ID
curl http://localhost:5001/get_transactions | jq '.[].entity_id'
```

## 📋 **Best Practices**

### **Entity ID Naming**
- **Use descriptive names**: `society_a`, `office_building`, `warehouse_1`
- **Avoid special characters**: Use only letters, numbers, underscores
- **Keep consistent**: Use same naming convention across controllers
- **Document mapping**: Keep track of Entity ID to location mapping

### **Deployment**
- **Test configuration** before production deployment
- **Backup data** before changing Entity IDs
- **Monitor Firestore usage** for cost optimization
- **Set up alerts** for each entity's activity

### **Maintenance**
- **Regular backups** of entity-specific data
- **Monitor storage usage** per entity
- **Clean up old data** periodically
- **Update Entity IDs** only when necessary

## 🔮 **Future Enhancements**

### **Planned Features**
- **Cross-entity user sharing** (optional)
- **Entity-level analytics** and reporting
- **Bulk entity management** tools
- **Entity-specific configuration** templates

### **Advanced Features**
- **Entity hierarchies** (parent-child relationships)
- **Multi-entity dashboards** for administrators
- **Entity-based access control** for web interface
- **Automated entity provisioning** for new deployments

---

## 📞 **Support**

For issues or questions about the entity-based system:
1. **Check logs** for entity-related errors
2. **Verify configuration** in web interface
3. **Test with provided script** for functionality
4. **Review Firestore structure** for data organization

The entity-based system provides a robust foundation for multi-controller deployments while maintaining the simplicity and reliability of the original single-controller system.
