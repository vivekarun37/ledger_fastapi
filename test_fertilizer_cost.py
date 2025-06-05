import requests
import json
from datetime import datetime, UTC

BASE_URL = "http://localhost:8000"

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
        "description": "Test farm for fertilizer cost testing",
        "client_code": "TESTFARM",
        "created_by": "system",
        "updated_by": "system"
    }
    
    print("\nCreating test client...")
    print(f"Using token: {auth_token}")
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

def test_fertilizer_cost():
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

    # Test data
    test_field = {
        "client_id": client_info["client_id"],
        "name": "Test Field",
        "planting_format": "rows",
        "status": "active",
        "location_type": "outdoor",
        "field_details": {
            "planting_data": {
                "test_crop_1": {
                    "crop_id": "test_crop_1",
                    "name": "Test Crop",
                    "tasks": [
                        {
                            "id": "task_1",
                            "name": "Apply Fertilizer",
                            "status": "pending",
                            "due_date": datetime.now(UTC).isoformat()
                        }
                    ]
                }
            }
        },
        "created_by": "system",
        "updated_by": "system"
    }

    # Step 4: Create a test field
    print("\nCreating test field...")
    response = requests.post(
        f"{BASE_URL}/add_field",
        json=test_field,
        headers=auth_headers
    )
    print(f"Create field response: {response.status_code}")
    print(response.json())
    
    if response.status_code == 200:
        field_id = response.json().get("id")
        
        # Get and print field data
        print("\nField data after creation:")
        response = requests.get(
            f"{BASE_URL}/get_fields?client_id={client_info['client_id']}",
            headers=auth_headers
        )
        if response.status_code == 200:
            fields = response.json()
            for field in fields:
                if field.get("_id") == field_id:
                    print(json.dumps(field, indent=2))
        
        # Step 5: Add fertilizer cost to the task
        cost_data = {
            "task_id": "task_1",
            "crop_id": "test_crop_1",
            "cost": 49.99,
            "description": "Test fertilizer application cost"
        }
        
        print("\nAdding fertilizer cost...")
        response = requests.put(
            f"{BASE_URL}/update_task_cost/{field_id}",
            json=cost_data,
            headers=auth_headers
        )
        print(f"Update task cost response: {response.status_code}")
        try:
            print(f"Response content: {response.json()}")
        except:
            print(f"Raw response content: {response.text}")
        
        # Step 6: Verify the field was updated
        print("\nVerifying field update...")
        response = requests.get(
            f"{BASE_URL}/get_fields?client_id={client_info['client_id']}",
            headers=auth_headers
        )
        print(f"Get fields response: {response.status_code}")
        if response.status_code == 200:
            fields = response.json()
            for field in fields:
                if field.get("_id") == field_id:
                    print("\nField data after update:")
                    print(json.dumps(field, indent=2))

if __name__ == "__main__":
    test_fertilizer_cost() 