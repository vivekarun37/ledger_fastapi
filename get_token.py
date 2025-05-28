import requests
import json

# Configuration
BASE_URL = "http://localhost:8023"  # Update this if your server runs on a different port
HEADERS = {
    "Content-Type": "application/json"
}

def get_token():
    print("\n=== Getting JWT Token ===")
    
    # Login data
    login_data = {
        "user_name": "admin",
        "password": "admin123"  # Replace with your actual password
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/getusers",
            headers=HEADERS,
            json=login_data
        )
        print(f"Login Response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nAccess Token:")
            print(data.get("access_token"))
            return data.get("access_token")
        else:
            print(f"Failed to login: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error getting token: {str(e)}")
        return None

if __name__ == "__main__":
    get_token() 