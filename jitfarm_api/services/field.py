from bson import ObjectId
from fastapi import HTTPException, status
from pymongo.errors import PyMongoError
from datetime import datetime
from jitfarm_api.models.farmModel import Fields
from typing import Dict, List, Optional, Any, Tuple
import json

class FieldService:
    def __init__(self, db_client):
        self.db_fields = db_client.fields
        self.db = db_client

    async def add_field(self, field: Fields) -> Tuple[Dict[str, str], Optional[Exception]]:
        try:
            field_data = field.dict()
            field_data["created_dt"] = datetime.utcnow().isoformat()
            field_data["updated_dt"] = datetime.utcnow().isoformat()
            
            result = await self.db_fields.insert_one(field_data)
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
            fields = []
            async for field in self.db_fields.find({"client_id": client_id}):
                field["_id"] = str(field["_id"])
                fields.append(field)
            return fields, None
        except PyMongoError as e:
            error_msg = f"Database error while retrieving fields for client {client_id}: {str(e)}"
            return [], e
        except Exception as e:
            error_msg = f"Unexpected error retrieving fields for client {client_id}: {str(e)}"
            return [], e

    async def get_field_by_id(self, field_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[Exception]]:
        try:
            if not ObjectId.is_valid(field_id):
                return None, ValueError("Invalid field ID format")
                
            field = await self.db_fields.find_one({"_id": ObjectId(field_id)})
            if field is None:
                return None, None
                
            field["_id"] = str(field["_id"])
            return field, None
        except PyMongoError as e:
            error_msg = f"Database error while retrieving field {field_id}: {str(e)}"
            return None, e
        except Exception as e:
            error_msg = f"Unexpected error retrieving field {field_id}: {str(e)}"
            return None, e

    async def update_field(self, field_id: str, field_data: dict) -> Tuple[Dict[str, str], Optional[Exception]]:
        try:
            if not ObjectId.is_valid(field_id):
                return {"status": "error", "message": "Invalid field ID format"}, ValueError("Invalid field ID format")
                
            field_data["updated_dt"] = datetime.utcnow().isoformat()
            
            result = await self.db_fields.update_one(
                {"_id": ObjectId(field_id)},
                {"$set": field_data}
            )
            
            if result.matched_count == 0:
                return {"status": "error", "message": "Field not found"}, None
                
            return {
                "status": "success",
                "message": "Field updated successfully"
            }, None
        except PyMongoError as e:
            error_msg = f"Database error: {str(e)}"
            return {"status": "error", "message": error_msg}, e
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
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

    async def update_task_cost(
        self, 
        field_id: str, 
        task_id: str, 
        cost: float, 
        crop_id: str,
        description: str,
        user_name: str
    ) -> Tuple[Dict[str, str], Optional[Exception]]:
        try:
            if not ObjectId.is_valid(field_id):
                return {"status": "error", "message": "Invalid field ID format"}, ValueError("Invalid field ID format")
            
            result = await self.db_fields.find_one({"_id": ObjectId(field_id)})
            if not result:
                return {"status": "error", "message": "Field not found"}, ValueError("Field not found")
            
            field_details = result.get("field_details", {})
            planting_data = field_details.get("planting_data", {})
            client_id = result.get("client_id")
            
            print(f"Field details: {json.dumps(field_details, indent=2)}")
            print(f"Planting data: {json.dumps(planting_data, indent=2)}")
            print(f"Looking for crop_id: {crop_id}")
            
            if not crop_id:
                return {"status": "error", "message": "Crop ID is required"}, ValueError("Crop ID is required")
            
            if crop_id not in planting_data:
                return {"status": "error", "message": f"Crop {crop_id} not found in field"}, ValueError("Crop not found")
            
            crop_data = planting_data[crop_id]
            tasks = crop_data.get("tasks", [])
            print(f"Tasks for crop {crop_id}: {json.dumps(tasks, indent=2)}")
            
            task_updated = False
            for task in tasks:
                print(f"Checking task: {json.dumps(task, indent=2)}")
                if task.get("id") == task_id:
                    print(f"Found matching task {task_id}, updating cost to {cost}")
                    task["cost"] = cost
                    task_updated = True
                    
                    # Create transaction for the cost
                    transaction_data = {
                        "client_id": client_id,
                        "transaction_type": "expense",
                        "amount": cost,
                        "date": datetime.utcnow().isoformat(),
                        "payee": "Internal",
                        "category": "Fertilizer",
                        "description": description,
                        "associated_to": task_id,
                        "keywords": "fertilizer,task",
                        "created_by": user_name,
                        "updated_by": user_name,
                        "created_dt": datetime.utcnow().isoformat(),
                        "updated_dt": datetime.utcnow().isoformat()
                    }
                    
                    # Add transaction to database
                    await self.db.transactions.insert_one(transaction_data)
                    break
            
            if not task_updated:
                return {"status": "error", "message": f"Task {task_id} not found for crop {crop_id}"}, ValueError("Task not found")
            
            # Update the tasks in the planting data
            crop_data["tasks"] = tasks
            planting_data[crop_id] = crop_data
            field_details["planting_data"] = planting_data
            
            print(f"Updated field details: {json.dumps(field_details, indent=2)}")
            
            await self.db_fields.update_one(
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
                "message": "Task cost updated successfully"
            }, None
            
        except PyMongoError as e:
            error_msg = f"Database error while updating task cost for field {field_id}, task {task_id}: {str(e)}"
            print(f"Error: {error_msg}")
            return {"status": "error", "message": error_msg}, e
        except Exception as e:
            error_msg = f"Unexpected error updating task cost for field {field_id}, task {task_id}: {str(e)}"
            print(f"Error: {error_msg}")
            return {"status": "error", "message": error_msg}, e

    async def delete_field(self, field_id: str) -> Tuple[Dict[str, str], Optional[Exception]]:
        try:
            if not ObjectId.is_valid(field_id):
                return {"status": "error", "message": "Invalid field ID format"}, ValueError("Invalid field ID format")
                
            result = await self.db_fields.delete_one({"_id": ObjectId(field_id)})
            
            if result.deleted_count == 0:
                return {"status": "error", "message": "Field not found"}, None
                
            return {
                "status": "success",
                "message": "Field deleted successfully"
            }, None
        except PyMongoError as e:
            error_msg = f"Database error: {str(e)}"
            return {"status": "error", "message": error_msg}, e
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            return {"status": "error", "message": error_msg}, e