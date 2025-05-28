from bson import ObjectId
from fastapi import HTTPException, status
from pymongo.errors import PyMongoError
from datetime import datetime
from jitfarm_api.models.farmModel import COAccount
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorCollection
import json

class COAccountService:
    def __init__(self, app):
        self.db_accounts = app.accounts 
        self.db = app
        self.transactions = app.transactions

    async def add_account(self, account: COAccount) -> Dict[str, str]:
        try:
            account_data = account.dict()
            
            # Check if account code already exists for this client
            existing_account = await self.db_accounts.find_one({
                "client_id": account_data["client_id"],
                "account_code": account_data["account_code"]
            })
            
            if existing_account:
                raise HTTPException(
                    status_code=400, 
                    detail="Account code already exists. Please use a different code."
                )
            
            result = await self.db_accounts.insert_one(account_data)
            return {
                "status": "success", 
                "message": "Account added successfully", 
                "id": str(result.inserted_id)
            }
        except HTTPException as e:
            raise e
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def get_accounts(self, client_id: str) -> List[Dict[str, Any]]:
        try:
            cursor = self.db_accounts.find({"client_id": client_id})
            accounts = []
            async for account in cursor:
                account["_id"] = str(account["_id"])
                accounts.append(account)
            return accounts

        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def update_account(self, account_id: str, account_data: Dict[str, Any]) -> Dict[str, str]:
        try:
            if not ObjectId.is_valid(account_id):
                raise HTTPException(status_code=400, detail="Invalid account ID format")

            existing_account = await self.db_accounts.find_one({"_id": ObjectId(account_id)})

            if not existing_account:
                raise HTTPException(status_code=404, detail="Account not found")
            
            # Handle child account creation if provided
            if "child_account" in account_data and account_data["child_account"]:
                # Check if parent account is a group account
                if not existing_account.get("is_group", False):
                    raise HTTPException(
                        status_code=400, 
                        detail="Cannot add child to a non-group account"
                    )
                
                child_data = account_data["child_account"]
                
                # Check if child account code already exists
                duplicate_check = await self.db_accounts.find_one({
                    "client_id": existing_account["client_id"],
                    "account_code": child_data.get("account_code")
                })
                
                if duplicate_check:
                    raise HTTPException(
                        status_code=400, 
                        detail="Account code already exists. Please use a different code."
                    )
                
                # Create the child account with proper parentage
                child_account = {
                    "account_name": child_data.get("account_name"),
                    "account_code": child_data.get("account_code"),
                    "account_type": child_data.get("account_type", existing_account.get("account_type")),
                    "account_subtype": child_data.get("account_subtype"),
                    "account_number": child_data.get("account_number", ""),
                    "description": child_data.get("description"),
                    "is_active": child_data.get("is_active", True),
                    "is_group": child_data.get("is_group", False),
                    "parent_id": account_id,
                    "children": [],
                    "client_id": child_data.get("client_id"),
                    "created_by": child_data.get("created_by"),
                    "created_dt": datetime.utcnow().isoformat(),
                    "updated_by": child_data.get("updated_by"),
                    "updated_dt": datetime.utcnow().isoformat()
                }
                
                # Insert the child account
                child_result = await self.db_accounts.insert_one(child_account)
                child_id = str(child_result.inserted_id)
                
                # Update the parent's children array
                await self.db_accounts.update_one(
                    {"_id": ObjectId(account_id)},
                    {"$push": {"children": child_id}}
                )
                
                # Return both parent and child information
                return {
                    "status": "success", 
                    "message": "Child account added successfully",
                    "parent_id": account_id,
                    "child_id": child_id
                }
            
            # Regular account update logic
            if "account_code" in account_data and account_data["account_code"] != existing_account.get("account_code"):
                duplicate_check = await self.db_accounts.find_one({
                    "_id": {"$ne": ObjectId(account_id)},
                    "client_id": existing_account["client_id"],
                    "account_code": account_data.get("account_code")
                })
                
                if duplicate_check:
                    raise HTTPException(
                        status_code=400, 
                        detail="Account code already exists. Please use a different code."
                    )

            update_data = {
                "account_name": account_data.get("account_name", existing_account.get("account_name")),
                "account_code": account_data.get("account_code", existing_account.get("account_code")),
                "account_type": account_data.get("account_type", existing_account.get("account_type")),
                "account_number": account_data.get("account_number", existing_account.get("account_number")),
                "account_subtype": account_data.get("account_subtype", existing_account.get("account_subtype")),
                "is_active": account_data.get("is_active", existing_account.get("is_active")),
                "is_group": account_data.get("is_group", existing_account.get("is_group")),
                "description": account_data.get("description", existing_account.get("description")),
                "updated_by": account_data.get("updated_by", existing_account.get("updated_by")),
                "updated_dt": datetime.utcnow().isoformat(),
            }

            await self.db_accounts.update_one({"_id": ObjectId(account_id)}, {"$set": update_data})

            return {"status": "success", "message": "Account updated successfully"}
        
        except HTTPException as e:
            raise e
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def delete_account(self, account_id: str) -> Dict[str, str]:
        try:
            if not ObjectId.is_valid(account_id):
                raise HTTPException(status_code=400, detail="Invalid account ID format")

            account_record = await self.db_accounts.find_one({"_id": ObjectId(account_id)})

            if not account_record:
                raise HTTPException(status_code=404, detail="Account not found")
                
            # TODO: Add logic to check if account is in use before deleting
            # For example, check if there are any journal entries or transactions referencing this account
            
            await self.db_accounts.delete_one({"_id": ObjectId(account_id)})
            
            return {
                "status": "success",
                "message": "Account deleted successfully",
            }
        except HTTPException as e:
            raise e
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def active_accounts(self, client_id: str) -> List[Dict[str, Any]]:
        try:
            cursor = self.db_accounts.find({"client_id": client_id, "is_active": True})
            accounts = []
            async for account in cursor:
                account["_id"] = str(account["_id"])
                accounts.append(account)
            return accounts

        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")