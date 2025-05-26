from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client.nextai

# 1. Create a test account
account = {
    "account_name": "Test Bank Account",
    "account_code": "BANK001",
    "account_type": "Asset",
    "account_subtype": "Current Asset",
    "description": "Test account",
    "is_active": True,
    "client_id": "TEST123",
    "created_by": "test",
    "updated_by": "test",
    "created_dt": datetime.utcnow().isoformat(),
    "updated_dt": datetime.utcnow().isoformat()
}

# Insert account and get its ID
account_id = str(db.accounts.insert_one(account).inserted_id)
print(f"Created account with ID: {account_id}")

# 2. Create some test transactions
transactions = [
    {
        "account_id": account_id,
        "date": datetime.utcnow().isoformat(),
        "type": "credit",
        "amount": 1000.00,
        "description": "Initial deposit",
        "client_id": "TEST123"
    },
    {
        "account_id": account_id,
        "date": datetime.utcnow().isoformat(),
        "type": "debit",
        "amount": 200.00,
        "description": "ATM withdrawal",
        "client_id": "TEST123"
    }
]

# Insert transactions
db.transactions.insert_many(transactions)
print("Added test transactions")

# 3. Print curl command for testing
print("\nTest with this curl command:")
print(f"curl -X GET 'http://127.0.0.1:8010/test_ledger/{account_id}'") 