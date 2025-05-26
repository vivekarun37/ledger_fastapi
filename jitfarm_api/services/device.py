from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import PyMongoError
from datetime import datetime
from models.farmModel import Device
from typing import Dict, List, Optional, Any

class DeviceService:
    def __init__(self, db_client):
        self.db_devices = db_client.devices
        self.db = db_client

    async def add_device(self, device: Device) -> Dict[str, str]:
        try:
            device_data = device.dict()
            result = self.db_devices.insert_one(device_data)
            return {
                "status": "success",
                "message": "Device added successfully",
                "id": str(result.inserted_id)
            }
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    async def get_devices(self, client_id: str) -> Dict[str, Any]:
        try:
            devices = list(self.db_devices.find({"client_id": client_id}))
            for device in devices:
                device["_id"] = str(device["_id"])
            return {
                "status": "success",
                "devices": devices
            }
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def update_device(self, device_id: str, device_data: Dict[str, Any]) -> Dict[str, str]:
        try:
            if not ObjectId.is_valid(device_id):
                raise HTTPException(status_code=400, detail="Invalid device ID format")

            existing_device = self.db_devices.find_one({"_id": ObjectId(device_id)})

            if not existing_device:
                raise HTTPException(status_code=404, detail="Device not found")

            # Core fields to update
            update_data = {
                "device_name": device_data.get("device_name", existing_device.get("device_name")),
                "device_type": device_data.get("device_type", existing_device.get("device_type")),
                "device_id": device_data.get("device_id", existing_device.get("device_id")),
                "client_id": existing_device["client_id"], 
                "created_by": existing_device["created_by"],
                "created_dt": existing_device["created_dt"],
                "updated_by": device_data.get("updated_by", existing_device.get("updated_by")),
                "updated_dt": datetime.utcnow(),
            }

            # Add any additional fields that may be in the device model
            for key, value in device_data.items():
                if key not in update_data and key not in ["_id", "client_id", "created_by", "created_dt"]:
                    update_data[key] = value

            self.db_devices.update_one({"_id": ObjectId(device_id)}, {"$set": update_data})

            return {
                "status": "success",
                "message": "Device updated successfully",
            }
        except HTTPException as e:
            # Re-raise HTTP exceptions to maintain their status codes
            raise e
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def delete_device(self, device_id: str) -> Dict[str, str]:
        try:
            if not ObjectId.is_valid(device_id):
                raise HTTPException(status_code=400, detail="Invalid device ID format")

            device_record = self.db_devices.find_one({"_id": ObjectId(device_id)})

            if not device_record:
                raise HTTPException(status_code=404, detail="Device not found")
                
            self.db_devices.delete_one({"_id": ObjectId(device_id)})
            
            return {
                "status": "success",
                "message": "Device deleted successfully",
            }
        except HTTPException as e:
            # Re-raise HTTP exceptions to maintain their status codes
            raise e
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def activate_devices(self, device_ids: List[str]) -> Dict[str, Any]:
        try:
            results = {
                "status": "success",
                "message": "Devices activated successfully",
                "activated": [],
                "failed": []
            }
            
            for device_id in device_ids:
                # First try to find by the device_id field
                device = self.db_devices.find_one({"device_id": device_id})
                
                # If not found and it looks like an ObjectId, try as _id
                if not device and ObjectId.is_valid(device_id):
                    device = self.db_devices.find_one({"_id": ObjectId(device_id)})
                
                if device:
                    # Update the device
                    update_result = self.db_devices.update_one(
                        {"_id": device["_id"]}, 
                        {"$set": {"is_active": True, "updated_dt": datetime.utcnow()}}
                    )
                    
                    if update_result.modified_count > 0:
                        results["activated"].append(device_id)
                    else:
                        results["failed"].append({"id": device_id, "reason": "No changes made"})
                else:
                    results["failed"].append({"id": device_id, "reason": "Device not found"})
            
            if len(results["failed"]) > 0 and len(results["activated"]) == 0:
                results["status"] = "error"
                results["message"] = "Failed to activate any devices"
            elif len(results["failed"]) > 0:
                results["status"] = "partial"
                results["message"] = "Some devices were activated, but others failed"
                
            return results
            
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    
    async def deactivate_devices(self, device_ids: List[str]) -> Dict[str, Any]:
        try:
            results = {
                "status": "success",
                "message": "Devices deactivated successfully",
                "deactivated": [],
                "failed": []
            }
            
            for device_id in device_ids:
                # First try to find by the device_id field
                device = self.db_devices.find_one({"device_id": device_id})
                
                # If not found and it looks like an ObjectId, try as _id
                if not device and ObjectId.is_valid(device_id):
                    device = self.db_devices.find_one({"_id": ObjectId(device_id)})
                
                if device:
                    # Update the device
                    update_result = self.db_devices.update_one(
                        {"_id": device["_id"]}, 
                        {"$set": {"is_active": False, "updated_dt": datetime.utcnow()}}
                    )
                    
                    if update_result.modified_count > 0:
                        results["deactivated"].append(device_id)
                    else:
                        results["failed"].append({"id": device_id, "reason": "No changes made"})
                else:
                    results["failed"].append({"id": device_id, "reason": "Device not found"})
            
            if len(results["failed"]) > 0 and len(results["deactivated"]) == 0:
                results["status"] = "error"
                results["message"] = "Failed to deactivate any devices"
            elif len(results["failed"]) > 0:
                results["status"] = "partial"
                results["message"] = "Some devices were deactivated, but others failed"
                
            return results
            
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")