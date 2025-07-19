from bson import ObjectId
from fastapi import HTTPException, status
from pymongo.errors import PyMongoError
from datetime import datetime
from models.farmModel import TransactionType
from typing import Dict, List, Optional, Any

class TransactionTypeService:
    def __init__(self, app):
        self.db_transaction_types = app.transaction_types
        self.db = app

    async def add_transaction_type(self, transaction_type: TransactionType) -> Dict[str, str]:
        try:
            data = transaction_type.dict()
            # Check for duplicate name for this client
            existing = await self.db_transaction_types.find_one({
                "client_id": data["client_id"],
                "name": data["name"]
            })
            if existing:
                raise HTTPException(status_code=400, detail="Transaction type name already exists.")
            result = await self.db_transaction_types.insert_one(data)
            return {"status": "success", "message": "Transaction type added successfully", "id": str(result.inserted_id)}
        except HTTPException as e:
            raise e
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def get_transaction_types(self, client_id: str) -> List[Dict[str, Any]]:
        try:
            cursor = self.db_transaction_types.find({"client_id": client_id})
            transaction_types = []
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                transaction_types.append(doc)
            return transaction_types
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def update_transaction_type(self, transaction_type_id: str, data: Dict[str, Any]) -> Dict[str, str]:
        try:
            if not ObjectId.is_valid(transaction_type_id):
                raise HTTPException(status_code=400, detail="Invalid transaction type ID format")
            existing = await self.db_transaction_types.find_one({"_id": ObjectId(transaction_type_id)})
            if not existing:
                raise HTTPException(status_code=404, detail="Transaction type not found")
            # Prevent duplicate name
            if "name" in data and data["name"] != existing["name"]:
                duplicate = await self.db_transaction_types.find_one({
                    "client_id": existing["client_id"],
                    "name": data["name"]
                })
                if duplicate:
                    raise HTTPException(status_code=400, detail="Transaction type name already exists.")
            update_data = {**existing, **data}
            update_data["updated_dt"] = datetime.utcnow().isoformat()
            await self.db_transaction_types.update_one({"_id": ObjectId(transaction_type_id)}, {"$set": update_data})
            return {"status": "success", "message": "Transaction type updated successfully"}
        except HTTPException as e:
            raise e
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def delete_transaction_type(self, transaction_type_id: str) -> Dict[str, str]:
        try:
            if not ObjectId.is_valid(transaction_type_id):
                raise HTTPException(status_code=400, detail="Invalid transaction type ID format")
            existing = await self.db_transaction_types.find_one({"_id": ObjectId(transaction_type_id)})
            if not existing:
                raise HTTPException(status_code=404, detail="Transaction type not found")
            await self.db_transaction_types.delete_one({"_id": ObjectId(transaction_type_id)})
            return {"status": "success", "message": "Transaction type deleted successfully"}
        except HTTPException as e:
            raise e
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}") 