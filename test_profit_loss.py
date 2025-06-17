import requests
import json
from datetime import datetime, timedelta, UTC

BASE_URL = "http://localhost:8006"

def login_superadmin():
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    print("Logging in as superadmin...")
    response = requests.post(
        f"{BASE_URL}/user/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print(f"Login response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Login data: {json.dumps(data, indent=2)}")
        if data.get("status") == "success":
            return data.get("access_token")
        print(f"Login failed: {data.get('message', 'Unknown error')}")
    else:
        print(f"Login failed: {response.text}")
    return None

def create_test_client(auth_token):
    client_data = {
        "name": "Test Farm",
        "description": "Test farm for P&L testing",
        "client_code": "TESTFARM",
        "created_by": "system",
        "updated_by": "system"
    }
    
    print("\nCreating test client...")
    response = requests.post(
        f"{BASE_URL}/addclient",
        json=client_data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth_token}"
        }
    )
    print(f"Create client response: {response.status_code}")
    print(response.text)
    
    if response.status_code == 200:
        result = response.json()
        return {
            "client_id": result.get("id"),
            "admin_username": result.get("admin_username")
        }
    return None

def login_client_admin(username):
    login_data = {
        "username": username,
        "password": "password"  # Default password for system-generated admin users
    }
    
    print("\nLogging in as client admin...")
    response = requests.post(
        f"{BASE_URL}/user/login",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print(f"Login response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    print(response.json())
    return None

def create_test_transactions(client_id, auth_token):
    # Create some test transactions
    transactions = [
        {
            "client_id": client_id,
            "transaction_type": "income",
            "amount": 1000.00,
            "date": (datetime.now(UTC) - timedelta(days=60)).isoformat(),
            "payee": "Customer A",
            "category": "Sales",
            "description": "Product sale",
            "created_by": "system",
            "updated_by": "system"
        },
        {
            "client_id": client_id,
            "transaction_type": "expense",
            "amount": 500.00,
            "date": (datetime.now(UTC) - timedelta(days=45)).isoformat(),
            "payee": "Supplier B",
            "category": "Materials",
            "description": "Raw materials",
            "created_by": "system",
            "updated_by": "system"
        },
        {
            "client_id": client_id,
            "transaction_type": "income",
            "amount": 1500.00,
            "date": (datetime.now(UTC) - timedelta(days=30)).isoformat(),
            "payee": "Customer C",
            "category": "Services",
            "description": "Consulting services",
            "created_by": "system",
            "updated_by": "system"
        },
        {
            "client_id": client_id,
            "transaction_type": "expense",
            "amount": 300.00,
            "date": (datetime.now(UTC) - timedelta(days=15)).isoformat(),
            "payee": "Utility Co",
            "category": "Utilities",
            "description": "Monthly utilities",
            "created_by": "system",
            "updated_by": "system"
        }
    ]
    
    print("\nCreating test transactions...")
    for transaction in transactions:
        response = requests.post(
            f"{BASE_URL}/add_transaction",
            json=transaction,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {auth_token}"
            }
        )
        print(f"Create transaction response: {response.status_code}")
        print(response.json())

def test_profit_loss():
    # Step 1: Login as superadmin
    superadmin_token = login_superadmin()
    if not superadmin_token:
        print("Failed to login as superadmin")
        return
        
    # Step 2: Create a test client
    client_info = create_test_client(superadmin_token)
    if not client_info:
        print("Failed to create test client")
        return
        
    # Step 3: Login as the client admin
    token = login_client_admin(client_info["admin_username"])
    if not token:
        print("Failed to get authentication token")
        return
        
    auth_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    # Step 4: Create test transactions
    create_test_transactions(client_info["client_id"], token)

    # Step 5: Get P&L report for last 3 months
    print("\nGetting P&L report for last 3 months...")
    response = requests.get(
        f"{BASE_URL}/profit_loss?client_id={client_info['client_id']}",
        headers=auth_headers
    )
    print(f"P&L report response: {response.status_code}")
    if response.status_code == 200:
        print("\nP&L Report:")
        print(json.dumps(response.json(), indent=2))

    # Step 6: Get P&L report by quarter
    print("\nGetting P&L report by quarter...")
    response = requests.get(
        f"{BASE_URL}/profit_loss?client_id={client_info['client_id']}&group_by=quarter",
        headers=auth_headers
    )
    print(f"P&L report response: {response.status_code}")
    if response.status_code == 200:
        print("\nP&L Report (by quarter):")
        print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_profit_loss() 