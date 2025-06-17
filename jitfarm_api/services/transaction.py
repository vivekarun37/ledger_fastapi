from bson import ObjectId
from pymongo.errors import PyMongoError
from fastapi import HTTPException, status
from jitfarm_api.models.farmModel import Transaction
from datetime import datetime
from typing import Dict, List, Optional, Any
import json

class TransactionService:
    def __init__(self, app):
        self.db_transactions = app.transactions  # Collection for transactions
        self.db = app

    async def add_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, str]:
        try:
            # Validate the transaction data
            if not transaction_data.get("client_id"):
                raise HTTPException(status_code=400, detail="Client ID is required")
            
            if not transaction_data.get("transaction_type"):
                raise HTTPException(status_code=400, detail="Transaction type is required")
            
            if not transaction_data.get("amount") or float(transaction_data.get("amount", 0)) <= 0:
                raise HTTPException(status_code=400, detail="Valid transaction amount is required")
            
            if not transaction_data.get("payee"):
                raise HTTPException(status_code=400, detail="Payee/Customer is required")
            
            if not transaction_data.get("category"):
                raise HTTPException(status_code=400, detail="Category is required")
            
            if not transaction_data.get("date"):
                raise HTTPException(status_code=400, detail="Transaction date is required")
            
            # Add created and updated timestamps
            if not transaction_data.get("created_dt"):
                transaction_data["created_dt"] = datetime.utcnow().isoformat()
                
            if not transaction_data.get("updated_dt"):
                transaction_data["updated_dt"] = datetime.utcnow().isoformat()
            
            result = await self.db_transactions.insert_one(transaction_data)
            
            return {
                "status": "success", 
                "message": "Transaction added successfully", 
                "id": str(result.inserted_id)
            }
        except HTTPException as e:
            raise e
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def get_transactions(self, client_id: str) -> List[Dict[str, Any]]:
        try:
            transactions = list(self.db_transactions.find({"client_id": client_id}))

            # Convert ObjectId to string for JSON serialization
            for transaction in transactions:
                transaction["_id"] = str(transaction["_id"])
                
                # Convert category ID to readable name if needed
                if "category" in transaction and ObjectId.is_valid(transaction["category"]):
                    try:
                        category = self.db.accounts.find_one({"_id": ObjectId(transaction["category"])})
                        if category:
                            transaction["category_name"] = category.get("account_name", "Unknown")
                    except:
                        # If error occurs, keep the category ID
                        pass
            
            return transactions

        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    
    async def get_all(self, client_id: str) -> List[Dict[str, Any]]:
        try:
            final = {}
            device_db= self.db.devices
            crop_db= self.db.crops
            field_db= self.db.fields
            final["devices"]= list(device_db.find({"client_id": client_id},{"device_name": 1, "_id": 1} ))
            final["crops"]= list(crop_db.find({"client_id": client_id},{"crop_name": 1, "_id": 1} ))
            final["fields"]= list(field_db.find({"client_id": client_id},{"name": 1, "_id": 1}))
            for collection in final:
                for result in final[collection]:
                    if "_id" in result:
                        result["_id"] = str(result["_id"])
            return final
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def update_transaction(self, transaction_id: str, transaction_data: Dict[str, Any]) -> Dict[str, str]:
        try:
            if not ObjectId.is_valid(transaction_id):
                raise HTTPException(status_code=400, detail="Invalid transaction ID format")

            existing_transaction = self.db_transactions.find_one({"_id": ObjectId(transaction_id)})

            if not existing_transaction:
                raise HTTPException(status_code=404, detail="Transaction not found")
            
            # Validate key fields
            if transaction_data.get("amount") is not None and float(transaction_data.get("amount", 0)) <= 0:
                raise HTTPException(status_code=400, detail="Valid transaction amount is required")
            
            if transaction_data.get("payee") == "":
                raise HTTPException(status_code=400, detail="Payee/Customer is required")
                
            if transaction_data.get("category") == "":
                raise HTTPException(status_code=400, detail="Category is required")
                
            if transaction_data.get("date") == "":
                raise HTTPException(status_code=400, detail="Transaction date is required")
            
            # Update the transaction fields, keeping existing values if not provided
            update_data = {key: value for key, value in transaction_data.items() if key != "_id"}
            
            # Always update the modified timestamp
            update_data["updated_dt"] = datetime.utcnow().isoformat()
            
            self.db_transactions.update_one({"_id": ObjectId(transaction_id)}, {"$set": update_data})

            return {"status": "success", "message": "Transaction updated successfully"}
        
        except HTTPException as e:
            raise e
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def delete_transaction(self, transaction_id: str) -> Dict[str, str]:
        try:
            if not ObjectId.is_valid(transaction_id):
                raise HTTPException(status_code=400, detail="Invalid transaction ID format")

            transaction_record = self.db_transactions.find_one({"_id": ObjectId(transaction_id)})

            if not transaction_record:
                raise HTTPException(status_code=404, detail="Transaction not found")
            
            # Check if there are any dependencies before deleting
            # For example, if transactions are linked to other records
            
            self.db_transactions.delete_one({"_id": ObjectId(transaction_id)})
            
            return {
                "status": "success",
                "message": "Transaction deleted successfully",
            }
        except HTTPException as e:
            raise e
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")