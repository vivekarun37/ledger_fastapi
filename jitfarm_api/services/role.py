from bson import ObjectId
from fastapi import HTTPException, status
from pymongo.errors import PyMongoError
from jitfarm_api.models.farmModel import Role
from datetime import datetime
from typing import Dict, List, Any
import json

class RoleService:
    def __init__(self, db):
        self.db_roles = db.roles
        self.db = db

    async def add_role(self, role_data: dict):
        try:
            # Ensure client_id is included in the role data
            if "client_id" not in role_data:
                raise HTTPException(status_code=400, detail="client_id is required")
                
            # Add timestamp data if not present
            if "created_dt" not in role_data:
                role_data["created_dt"] = datetime.utcnow()
                
            # Make sure we're using the correct database collection
            if not hasattr(self, 'db_roles'):
                raise ValueError("Database collection 'db_roles' is not properly initialized")
                
            # Perform insertion
            result = await self.db_roles.insert_one(role_data)
            
            # Return the inserted ID
            return str(result.inserted_id)
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def get_all_roles(self, client_id: str = None):
        try:
            # If client_id is provided, filter by it
            query = {"client_id": client_id} if client_id else {}
            
            roles = await self.db_roles.find(query).to_list(length=None)
            
            for role in roles:
                role["_id"] = str(role["_id"])
            
            return roles
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def get_role_by_id(self, role_id: str):
        try:
            if not ObjectId.is_valid(role_id):
                raise HTTPException(status_code=400, detail="Invalid role ID format")
                
            role = await self.db_roles.find_one({"_id": ObjectId(role_id)})
            if role is None:
                raise HTTPException(status_code=404, detail="Role not found")
                
            role["_id"] = str(role["_id"])
            return role
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def get_roles_by_client(self, client_id: str):
        try:
            roles = []
            async for role in self.db_roles.find({"client_id": client_id}):
                role["_id"] = str(role["_id"])
                roles.append(role)
            return roles
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def update_role(self, role_id: str, role_data: dict):
        try:
            if not ObjectId.is_valid(role_id):
                raise HTTPException(status_code=400, detail="Invalid role ID format")
                
            existing_role = await self.db_roles.find_one({"_id": ObjectId(role_id)})
            if existing_role is None:
                raise HTTPException(status_code=404, detail="Role not found")
                
            result = await self.db_roles.update_one(
                {"_id": ObjectId(role_id)},
                {"$set": role_data}
            )
            
            return {"message": "Role updated successfully"} if result.modified_count > 0 else {"message": "No changes made"}
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def delete_role(self, role_id: str):
        try:
            if not ObjectId.is_valid(role_id):
                raise HTTPException(status_code=400, detail="Invalid role ID format")
                
            existing_role = await self.db_roles.find_one({"_id": ObjectId(role_id)})
            if existing_role is None:
                raise HTTPException(status_code=404, detail="Role not found")
                
            result = await self.db_roles.delete_one({"_id": ObjectId(role_id)})
            
            return {"message": "Role deleted successfully"} if result.deleted_count > 0 else {"message": "No role deleted"}
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def get_role_permissions(self, role_id: str):
        try:
            if not ObjectId.is_valid(role_id):
                raise HTTPException(status_code=400, detail="Invalid role ID format")
                
            role = await self.db_roles.find_one({"_id": ObjectId(role_id)})
            if role is None:
                raise HTTPException(status_code=404, detail="Role not found")
                
            return role.get("permissions", {})
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def update_role_permissions(self, role_id: str, permissions: dict):
        try:
            if not ObjectId.is_valid(role_id):
                raise HTTPException(status_code=400, detail="Invalid role ID format")
                
            existing_role = await self.db_roles.find_one({"_id": ObjectId(role_id)})
            if existing_role is None:
                raise HTTPException(status_code=404, detail="Role not found")
                
            result = await self.db_roles.update_one(
                {"_id": ObjectId(role_id)},
                {"$set": {"permissions": permissions}}
            )
            
            return {"message": "Role permissions updated successfully"} if result.modified_count > 0 else {"message": "No changes made"}
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    async def get_all_permissions(self):
        try:
            permissions = await self.db.permissions.find().to_list(length=None)
            if not permissions:
                return []
                
            for permission in permissions:
                permission["_id"] = str(permission["_id"])
                
            return permissions
        except Exception as e:
            # Log the actual exception for better debugging
            print(f"Error fetching permissions: {str(e)}")
            raise Exception(f"An error occurred while fetching permissions: {str(e)}")