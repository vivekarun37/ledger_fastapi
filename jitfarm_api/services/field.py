from bson import ObjectId
from fastapi import HTTPException, status
from pymongo.errors import PyMongoError
from datetime import datetime
from jitfarm_api.models.farmModel import Field
from typing import Dict, List, Optional, Any, Tuple
import json

class FieldService:
    def __init__(self, db_client):
        self.db_fields = db_client.fields
        self.db = db_client

    async def add_field(self, field: Field) -> Tuple[Dict[str, str], Optional[Exception]]:
        try:
            field_data = field.dict()
            field_data["created_dt"] = datetime.utcnow().isoformat()
            field_data["updated_dt"] = datetime.utcnow().isoformat()
            
            result = self.db_fields.insert_one(field_data)
            return {
                "status": "success",
                "message": "Field added successfully",
                "id": str(result.inserted_id)
            }, None
        except PyMongoError as e:
            error_msg = f"Database error: {str(e)}"
            return {"status": "error", "message": error_msg}, e
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            return {"status": "error", "message": error_msg}, e

    async def get_fields(self, client_id: str) -> Tuple[List[Dict[str, Any]], Optional[Exception]]:
        try:
            fields = list(self.db_fields.find({"client_id": client_id}))
            for field in fields:
                field["_id"] = str(field["_id"])
            return fields, None
        except PyMongoError as e:
            error_msg = f"Database error while retrieving fields for client {client_id}: {str(e)}"
            return [], e
        except Exception as e:
            error_msg = f"Unexpected error retrieving fields for client {client_id}: {str(e)}"
            return [], e

    async def update_field(self, field_id: str, field_data: Dict[str, Any]) -> Tuple[Dict[str, str], Optional[Exception]]:
        try:
            # Validate field_id format
            if not ObjectId.is_valid(field_id):
                return {"status": "error", "message": "Invalid field ID format"}, ValueError("Invalid field ID format")
                
            # Find existing field
            existing_field = self.db_fields.find_one({"_id": ObjectId(field_id)})
            if not existing_field:
                return {"status": "error", "message": "Field not found"}, ValueError("Field not found")
                
            # Prepare update data
            update_data = field_data.copy()
            update_data["updated_dt"] = datetime.utcnow().isoformat()
            update_data.pop("_id", None)  # Prevent modifying "_id"
            
            if "planting_data" in field_data:
                existing_plantings = existing_field.get("planting_data", [])
                incoming_plantings = field_data["planting_data"]
                
                if isinstance(incoming_plantings, list):
                    update_data["planting_data"] = incoming_plantings
                else:
                    return {"status": "error", "message": "Invalid format for planting_data"}, ValueError("Invalid format for planting_data")
            
            # Handle device_data differently - replace instead of append
            if "device_data" in field_data:
                incoming_device_data = field_data["device_data"]
                
                if isinstance(incoming_device_data, dict):
                    update_data["device_data"] = incoming_device_data
                else:
                    return {"status": "error", "message": "Invalid format for device_data"}, ValueError("Invalid format for device_data")
            
            self.db_fields.update_one({"_id": ObjectId(field_id)}, {"$set": update_data})
            
            return {
                "status": "success",
                "message": "Field updated successfully"
            }, None
        except PyMongoError as e:
            error_msg = f"Database error while updating field {field_id}: {str(e)}"
            return {"status": "error", "message": error_msg}, e
        except Exception as e:
            error_msg = f"Unexpected error updating field {field_id}: {str(e)}"
            return {"status": "error", "message": error_msg}, e

    async def update_field_devices(self, field_id: str, device_data: Dict[str, Any]) -> Tuple[Dict[str, str], Optional[Exception]]:
        try:
            # Validate field_id format
            if not ObjectId.is_valid(field_id):
                return {"status": "error", "message": "Invalid field ID format"}, ValueError("Invalid field ID format")
                
            result = self.db_fields.update_one(
                {"_id": ObjectId(field_id)},
                {"$set": {"device_data": device_data["device_data"], "updated_dt": datetime.utcnow().isoformat()}}
            )
            
            if result.matched_count == 0:
                return {"status": "error", "message": "Field not found"}, ValueError("Field not found")
                
            if result.modified_count == 0:
                return {"status": "warning", "message": "No changes were made"}, None
                
            return {
                "status": "success",
                "message": "Field devices updated successfully",
                "field_id": field_id
            }, None
        except PyMongoError as e:
            error_msg = f"Database error while updating devices for field {field_id}: {str(e)}"
            return {"status": "error", "message": error_msg}, e
        except Exception as e:
            error_msg = f"Unexpected error updating devices for field {field_id}: {str(e)}"
            return {"status": "error", "message": error_msg}, e

    async def update_task_status(self, field_id: str, task_id: str, new_status: str, crop_id: str) -> Tuple[Dict[str, str], Optional[Exception]]:
        try:
            if not ObjectId.is_valid(field_id):
                return {"status": "error", "message": "Invalid field ID format"}, ValueError("Invalid field ID format")

            valid_statuses = ["pending", "completed", "missed", "in-progress"]
            if new_status not in valid_statuses:
                return {"status": "error", "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}, ValueError("Invalid status value")
            
            result = self.db_fields.find_one({"_id": ObjectId(field_id)})
            if not result:
                return {"status": "error", "message": "Field not found"}, ValueError("Field not found")
            
            field_details = result.get("field_details", {})
            planting_data = field_details.get("planting_data", [])
            
            task_updated = False
            
            for data in planting_data:
                if data.get("crop_id") == crop_id:
                    tasks = data.get("tasks", [])
                    for task in tasks:
                        if task.get("id") == task_id:
                            task["status"] = new_status
                            task_updated = True
                            print(f"Successfully updated task status to {new_status}")
                            break
                    
                    if task_updated:
                        break
            
            if not task_updated:
                return {"status": "error", "message": f"Task {task_id} not found for crop {crop_id}"}, ValueError("Task not found")
            
            field_details["planting_data"] = planting_data
            
            self.db_fields.update_one(
                {"_id": ObjectId(field_id)},
                {
                    "$set": {
                        "field_details": field_details,
                        "updated_dt": datetime.utcnow().isoformat()
                    }
                }
            )
            
            return {
                "status": "success",
                "message": "Task status updated successfully"
            }, None
            
        except PyMongoError as e:
            error_msg = f"Database error while updating task status for field {field_id}, task {task_id}: {str(e)}"
            return {"status": "error", "message": error_msg}, e
        except Exception as e:
            error_msg = f"Unexpected error updating task status for field {field_id}, task {task_id}: {str(e)}"
            return {"status": "error", "message": error_msg}, e


    async def delete_field(self, field_id: str) -> Tuple[Dict[str, str], Optional[Exception]]:
        try:
            if not ObjectId.is_valid(field_id):
                return {"status": "error", "message": "Invalid field ID format"}, ValueError("Invalid field ID format")

            field_record = self.db_fields.find_one({"_id": ObjectId(field_id)})
            
            if not field_record:
                return {"status": "error", "message": "Field not found"}, ValueError("Field not found")
                
            self.db_fields.delete_one({"_id": ObjectId(field_id)})
            
            return {
                "status": "success",
                "message": "Field deleted successfully"
            }, None
        except PyMongoError as e:
            error_msg = f"Database error while deleting field {field_id}: {str(e)}"
            return {"status": "error", "message": error_msg}, e
        except Exception as e:
            error_msg = f"Unexpected error deleting field {field_id}: {str(e)}"
            return {"status": "error", "message": error_msg}, e