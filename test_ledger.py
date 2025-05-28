import asyncio
import json
import httpx
import logging
from datetime import datetime, timezone

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:8023"
COA_ID = "6830ba643637b047ee5855cb"  # Your COA ID
USERNAME = "admin"
PASSWORD = "admin123"

async def login() -> str:
    """Login and get access token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/user/login",
            data={"username": USERNAME, "password": PASSWORD}
        )
        if response.status_code != 200:
            raise Exception(f"Login failed: {response.text}")
        return response.json()["access_token"]

async def test_create_ledger_entry(token: str) -> str:
    """Test creating a ledger entry"""
    entry_data = {
        "coa_id": COA_ID,
        "transaction_date": datetime.now(timezone.utc).isoformat(),
        "description": "Test ledger entry",
        "debit": 1000.00,
        "credit": 0.00,
        "reference": "TEST-001",
        "created_by": USERNAME,
        "created_dt": datetime.now(timezone.utc).isoformat(),
        "updated_by": USERNAME,
        "updated_dt": datetime.now(timezone.utc).isoformat()
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/ledger/entry",
            json=entry_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        logger.info(f"Create ledger entry response: {response.text}")
        if response.status_code != 200:
            raise Exception(f"Create ledger entry failed: {response.text}")
        
        result = response.json()
        return result["id"]  # Return the entry ID for further testing

async def test_get_ledger_entries(token: str):
    """Test getting ledger entries"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/ledger/entries/{COA_ID}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        logger.info(f"Get ledger entries response: {response.text}")
        if response.status_code != 200:
            raise Exception(f"Get ledger entries failed: {response.text}")

async def test_get_ledger_balance(token: str):
    """Test getting ledger balance"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/ledger/balance/{COA_ID}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        logger.info(f"Get ledger balance response: {response.text}")
        if response.status_code != 200:
            raise Exception(f"Get ledger balance failed: {response.text}")

async def test_update_ledger_entry(token: str, entry_id: str):
    """Test updating a ledger entry"""
    update_data = {
        "description": "Updated test ledger entry",
        "debit": 1500.00,
        "credit": 0.00
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{BASE_URL}/ledger/entry/{entry_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        logger.info(f"Update ledger entry response: {response.text}")
        if response.status_code != 200:
            raise Exception(f"Update ledger entry failed: {response.text}")

async def test_delete_ledger_entry(token: str, entry_id: str):
    """Test deleting a ledger entry"""
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{BASE_URL}/ledger/entry/{entry_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        logger.info(f"Delete ledger entry response: {response.text}")
        if response.status_code != 200:
            raise Exception(f"Delete ledger entry failed: {response.text}")

async def main():
    try:
        # Login and get token
        logger.info("Logging in...")
        token = await login()
        logger.info("Successfully logged in")

        # Test create entry
        logger.info("Testing create ledger entry...")
        entry_id = await test_create_ledger_entry(token)
        logger.info(f"Successfully created ledger entry with ID: {entry_id}")

        # Test get entries
        logger.info("Testing get ledger entries...")
        await test_get_ledger_entries(token)
        logger.info("Successfully retrieved ledger entries")

        # Test get balance
        logger.info("Testing get ledger balance...")
        await test_get_ledger_balance(token)
        logger.info("Successfully retrieved ledger balance")

        # Test update entry
        logger.info("Testing update ledger entry...")
        await test_update_ledger_entry(token, entry_id)
        logger.info("Successfully updated ledger entry")

        # Test delete entry
        logger.info("Testing delete ledger entry...")
        await test_delete_ledger_entry(token, entry_id)
        logger.info("Successfully deleted ledger entry")

        logger.info("All tests completed successfully!")

    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 