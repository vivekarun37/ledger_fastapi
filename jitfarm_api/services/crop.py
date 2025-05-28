from bson import ObjectId
from fastapi import HTTPException, status
from pymongo.errors import PyMongoError
from datetime import datetime
from jitfarm_api.models.farmModel import Crops
from typing import Dict, List, Optional, Any
import json

class CropService:
    def __init__(self, db_client):
        self.db_crops = db_client.crops
        self.db = db_client

    async def add_crop(self, crop: Crops) -> Dict[str, str]:
        try:
            crop_data = crop.dict()
            result = self.db_crops.insert_one(crop_data)
            return {
                "status": "success", 
                "message": "Crop added successfully", 
                "id": str(result.inserted_id)
            }
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def get_crops(self, client_id: str) -> List[Dict[str, Any]]:
        try:
            crops = list(self.db_crops.find({"client_id": client_id}))

            for crop in crops:
                crop["_id"] = str(crop["_id"])
                crop["custom_fields"] = crop.get("custom_fields", [])
                crop["tasks"] = crop.get("tasks", [])
            
            return crops

        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


    async def update_crop(self, crop_id: str, crop_data: Dict[str, Any]) -> Dict[str, str]:
        try:
            if not ObjectId.is_valid(crop_id):
                raise HTTPException(status_code=400, detail="Invalid crop ID format")

            existing_crop = self.db_crops.find_one({"_id": ObjectId(crop_id)})

            if not existing_crop:
                raise HTTPException(status_code=404, detail="Crop not found")

            update_data = {
                "crop_name": crop_data.get("crop_name", existing_crop.get("crop_name")),
                "crop_variety": crop_data.get("crop_variety", existing_crop.get("crop_variety")),
                "crop_id": crop_data.get("crop_id", existing_crop.get("crop_id")),
                "client_id": existing_crop["client_id"],
                "created_by": existing_crop["created_by"],
                "created_dt": existing_crop["created_dt"],
                "updated_by": crop_data.get("updated_by", existing_crop.get("updated_by")),
                "updated_dt": datetime.utcnow(),
            }

            if "planting_data" in crop_data:
                update_data["planting_data"] = {**existing_crop.get("planting_data", {}), **crop_data["planting_data"]}
            if "harvest_data" in crop_data:
                update_data["harvest_data"] = {**existing_crop.get("harvest_data", {}), **crop_data["harvest_data"]}

            if "custom_fields" in crop_data:
                update_data["custom_fields"] = crop_data["custom_fields"]
            
            if "tasks" in crop_data:
                update_data["tasks"] = crop_data["tasks"]
            

            self.db_crops.update_one({"_id": ObjectId(crop_id)}, {"$set": update_data})

            return {"status": "success", "message": "Crop updated successfully"}
        
        except HTTPException as e:
            raise e
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


    async def delete_crop(self, crop_id: str) -> Dict[str, str]:
        try:
            if not ObjectId.is_valid(crop_id):
                raise HTTPException(status_code=400, detail="Invalid crop ID format")

            crop_record = self.db_crops.find_one({"_id": ObjectId(crop_id)})

            if not crop_record:
                raise HTTPException(status_code=404, detail="Crop not found")
                
            self.db_crops.delete_one({"_id": ObjectId(crop_id)})
            
            return {
                "status": "success",
                "message": "Crop deleted successfully",
            }
        except HTTPException as e:
            raise e
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")