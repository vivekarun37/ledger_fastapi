import requests
import json
from datetime import datetime, timedelta, UTC

BASE_URL = "http://localhost:8006"

def login_superadmin():
    login_data = {
        "user_name": "admin",
        "password": "admin123"
    }
    
    print("Logging in as superadmin...")
    response = requests.post(
        f"{BASE_URL}/user/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
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
        "user_name": username,
        "password": "password"  # Default password for system-generated admin users
    }
    
    print("\nLogging in as client admin...")
    response = requests.post(
        f"{BASE_URL}/user/login",
        json=login_data,
        headers={"Content-Type": "application/json"}
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

def create_test_accounts(client_id, auth_token):
    accounts = [
        {
            "account_name": "Cash",
            "account_code": "1000",
            "account_type": "Asset",
            "account_subtype": "Current Asset",
            "description": "Cash in hand",
            "is_active": True,
            "is_group": False,
            "client_id": client_id,
            "created_by": "system",
            "updated_by": "system"
        },
        {
            "account_name": "Accounts Payable",
            "account_code": "2000",
            "account_type": "Liability",
            "account_subtype": "Current Liability",
            "description": "Money owed to suppliers",
            "is_active": True,
            "is_group": False,
            "client_id": client_id,
            "created_by": "system",
            "updated_by": "system"
        },
        {
            "account_name": "Owner's Equity",
            "account_code": "3000",
            "account_type": "Equity",
            "account_subtype": "Owner's Equity",
            "description": "Owner's capital",
            "is_active": True,
            "is_group": False,
            "client_id": client_id,
            "created_by": "system",
            "updated_by": "system"
        }
    ]
    print("\nCreating test accounts...")
    account_ids = []
    for acc in accounts:
        response = requests.post(
            f"{BASE_URL}/add_account",
            json=acc,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {auth_token}"
            }
        )
        print(f"Create account response: {response.status_code}")
        print(response.text)
        if response.status_code == 200:
            result = response.json()
            account_ids.append(result.get("id"))
    return account_ids

def create_test_ledger_entries(client_id, account_ids, auth_token):
    # Assume account_ids order: [Asset, Liability, Equity]
    now = datetime.now(UTC)
    entries = [
        {
            "coa_id": account_ids[0],
            "transaction_date": (now - timedelta(days=10)).isoformat(),
            "description": "Initial cash deposit",
            "debit_amount": 5000.0,
            "credit_amount": 0.0,
            "created_by": "system",
            "is_active": True
        },
        {
            "coa_id": account_ids[1],
            "transaction_date": (now - timedelta(days=5)).isoformat(),
            "description": "Supplier invoice",
            "debit_amount": 0.0,
            "credit_amount": 1200.0,
            "created_by": "system",
            "is_active": True
        },
        {
            "coa_id": account_ids[2],
            "transaction_date": (now - timedelta(days=2)).isoformat(),
            "description": "Owner investment",
            "debit_amount": 0.0,
            "credit_amount": 3800.0,
            "created_by": "system",
            "is_active": True
        }
    ]
    print("\nCreating test ledger entries...")
    for entry in entries:
        response = requests.post(
            f"{BASE_URL}/ledger/add_ledger_entry",
            json={**entry, "client_id": client_id},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {auth_token}"
            }
        )
        print(f"Create ledger entry response: {response.status_code}")
        print(response.text)

def test_balance_sheet():
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
    # Step 4: Create test accounts
    account_ids = create_test_accounts(client_info["client_id"], token)
    if not account_ids or len(account_ids) < 3:
        print("Failed to create test accounts")
        return
    # Step 5: Create test ledger entries
    create_test_ledger_entries(client_info["client_id"], account_ids, token)
    auth_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    # Step 6: Get Balance Sheet report for current month
    print("\nGetting Balance Sheet report for current month...")
    response = requests.get(
        f"{BASE_URL}/balance_sheet?client_id={client_info['client_id']}",
        headers=auth_headers
    )
    print(f"Balance Sheet report response: {response.status_code}")
    if response.status_code == 200:
        print("\nBalance Sheet Report:")
        print(json.dumps(response.json(), indent=2))
    # Step 7: Get Balance Sheet report consolidated
    print("\nGetting Balance Sheet report (consolidated)...")
    response = requests.get(
        f"{BASE_URL}/balance_sheet?client_id={client_info['client_id']}&consolidate=true",
        headers=auth_headers
    )
    print(f"Balance Sheet report response: {response.status_code}")
    if response.status_code == 200:
        print("\nBalance Sheet Report (consolidated):")
        print(json.dumps(response.json(), indent=2))

def test_transaction_types():
    superadmin_token = login_superadmin()
    if not superadmin_token:
        print("Failed to login as superadmin")
        return
    client_info = create_test_client(superadmin_token)
    if not client_info:
        print("Failed to create test client")
        return
    token = login_client_admin(client_info["admin_username"])
    if not token:
        print("Failed to get authentication token")
        return
    auth_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    transactions = [
        {
            "client_id": client_info["client_id"],
            "transaction_type": "income",
            "amount": 1234.56,
            "date": datetime.now(UTC).isoformat(),
            "payee": "Test Payee",
            "category": "Test Income",
            "description": "Test income transaction",
            "created_by": "system",
            "updated_by": "system"
        },
        {
            "client_id": client_info["client_id"],
            "transaction_type": "expense",
            "amount": 654.32,
            "date": datetime.now(UTC).isoformat(),
            "payee": "Test Payee",
            "category": "Test Expense",
            "description": "Test expense transaction",
            "created_by": "system",
            "updated_by": "system"
        }
    ]
    print("\nTesting /add_transaction endpoint for income and expense...")
    for tx in transactions:
        response = requests.post(
            f"{BASE_URL}/add_transaction",
            json=tx,
            headers=auth_headers
        )
        print(f"Add transaction ({tx['transaction_type']}) response: {response.status_code}")
        print(response.json())

if __name__ == "__main__":
    test_profit_loss()
    test_balance_sheet()
    test_transaction_types() 