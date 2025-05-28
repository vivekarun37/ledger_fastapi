from datetime import datetime, UTC
from bson import ObjectId
from typing import Dict, List, Optional
from jitfarm_api.models.ledgerModel import LedgerEntry, LedgerUpdate
from motor.motor_asyncio import AsyncIOMotorCollection
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class LedgerService:
    def __init__(self, ledger_collection: AsyncIOMotorCollection, coa_collection: AsyncIOMotorCollection):
        self.ledger = ledger_collection
        self.coa = coa_collection

    async def create_ledger_entry(self, entry: LedgerEntry) -> Dict:
        try:
            # Verify COA exists
            coa = await self.coa.find_one({"_id": ObjectId(entry.coa_id)})
            if not coa:
                raise HTTPException(status_code=404, detail="Chart of Account not found")

            # Convert entry to dict and handle datetime fields
            entry_dict = entry.dict()
            entry_dict["created_dt"] = datetime.now(UTC)
            
            # Ensure transaction_date is a datetime object
            if isinstance(entry_dict["transaction_date"], str):
                try:
                    entry_dict["transaction_date"] = datetime.fromisoformat(entry_dict["transaction_date"].replace("Z", "+00:00"))
                except Exception as e:
                    logger.error(f"Error parsing transaction_date: {str(e)}")
                    raise HTTPException(status_code=400, detail="Invalid transaction_date format")
            
            try:
                result = await self.ledger.insert_one(entry_dict)
                return {
                    "status": "success",
                    "message": "Ledger entry created successfully",
                    "id": str(result.inserted_id)
                }
            except Exception as e:
                logger.error(f"Error inserting ledger entry: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error creating ledger entry: {str(e)}")
                
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Unexpected error in create_ledger_entry: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error creating ledger entry: {str(e)}")

    async def get_ledger_entries(self, coa_id: str, skip: int = 0, limit: int = 100) -> List[Dict]:
        try:
            cursor = self.ledger.find(
                {"coa_id": coa_id, "is_active": True}
            ).sort("transaction_date", -1).skip(skip).limit(limit)
            
            entries = []
            async for entry in cursor:
                entry["_id"] = str(entry["_id"])
                entries.append(entry)
            
            return entries
        except Exception as e:
            logger.error(f"Error fetching ledger entries: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching ledger entries: {str(e)}")

    async def get_ledger_entry(self, entry_id: str) -> Dict:
        try:
            entry = await self.ledger.find_one({"_id": ObjectId(entry_id), "is_active": True})
            if not entry:
                raise HTTPException(status_code=404, detail="Ledger entry not found")
            
            entry["_id"] = str(entry["_id"])
            return entry
        except Exception as e:
            logger.error(f"Error fetching ledger entry: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching ledger entry: {str(e)}")

    async def update_ledger_entry(self, entry_id: str, update_data: LedgerUpdate) -> Dict:
        try:
            # Verify entry exists
            entry = await self.ledger.find_one({"_id": ObjectId(entry_id), "is_active": True})
            if not entry:
                raise HTTPException(status_code=404, detail="Ledger entry not found")

            update_dict = {k: v for k, v in update_data.dict(exclude_unset=True).items() if v is not None}
            update_dict["updated_dt"] = datetime.now(UTC)

            # Handle transaction_date if it's being updated
            if "transaction_date" in update_dict and isinstance(update_dict["transaction_date"], str):
                try:
                    update_dict["transaction_date"] = datetime.fromisoformat(update_dict["transaction_date"].replace("Z", "+00:00"))
                except Exception as e:
                    logger.error(f"Error parsing transaction_date in update: {str(e)}")
                    raise HTTPException(status_code=400, detail="Invalid transaction_date format")

            result = await self.ledger.update_one(
                {"_id": ObjectId(entry_id)},
                {"$set": update_dict}
            )

            if result.modified_count == 0:
                raise HTTPException(status_code=400, detail="No changes made to the ledger entry")

            return {
                "status": "success",
                "message": "Ledger entry updated successfully"
            }
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"Error updating ledger entry: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error updating ledger entry: {str(e)}")

    async def delete_ledger_entry(self, entry_id: str, user: str) -> Dict:
        try:
            # Soft delete by setting is_active to False
            result = await self.ledger.update_one(
                {"_id": ObjectId(entry_id), "is_active": True},
                {
                    "$set": {
                        "is_active": False,
                        "updated_by": user,
                        "updated_dt": datetime.now(UTC)
                    }
                }
            )

            if result.modified_count == 0:
                raise HTTPException(status_code=404, detail="Ledger entry not found or already deleted")

            return {
                "status": "success",
                "message": "Ledger entry deleted successfully"
            }
        except Exception as e:
            logger.error(f"Error deleting ledger entry: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error deleting ledger entry: {str(e)}")

    async def get_ledger_balance(self, coa_id: str) -> Dict:
        try:
            pipeline = [
                {"$match": {"coa_id": coa_id, "is_active": True}},
                {"$group": {
                    "_id": None,
                    "total_debit": {"$sum": "$debit_amount"},
                    "total_credit": {"$sum": "$credit_amount"}
                }}
            ]
            
            result = await self.ledger.aggregate(pipeline).to_list(length=1)
            
            if not result:
                return {"balance": 0.0, "total_debit": 0.0, "total_credit": 0.0}
            
            balance = result[0]["total_debit"] - result[0]["total_credit"]
            return {
                "balance": balance,
                "total_debit": result[0]["total_debit"],
                "total_credit": result[0]["total_credit"]
            }
        except Exception as e:
            logger.error(f"Error calculating ledger balance: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error calculating ledger balance: {str(e)}") 