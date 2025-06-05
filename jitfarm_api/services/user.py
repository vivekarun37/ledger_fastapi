import bcrypt
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from bson import ObjectId
import traceback
import inspect
from datetime import datetime
from jitfarm_api.utils import create_access_token, decode_token
from datetime import timedelta
import hashlib
from pymongo.errors import PyMongoError
from jitfarm_api.models.farmModel import Users
from motor.motor_asyncio import AsyncIOMotorCollection
import json
import logging

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, db_users, db_clients, db_logs=None, db_error_log=None):
        self.db_users = db_users
        self.db_clients = db_clients
        self.db_logs = db_logs
        self.db_error_log = db_error_log

    def hash_password(self, password: str) -> str:
        return hashlib.md5(password.encode()).hexdigest()

    async def authenticate_user(self, user_name: str, password: str):
        try:
            # Hash the password for comparison
            hashed_password = self.hash_password(password)
            
            # Find the user
            found_user = await self.db_users.find_one({
                "user_name": user_name,
                "password": hashed_password
            })
            
            if not found_user:
                return None
                
            # Get client info
            client_id = found_user.get("client_id")
            client_name = None
            client_code = None
            
            if client_id:
                try:
                    # Handle both ObjectId and string client_id
                    if isinstance(client_id, str):
                        client_id = ObjectId(client_id)
                    find_client = await self.db_clients.find_one({"_id": client_id})
                    if find_client:
                        client_name = find_client.get("name", None)
                        client_code = find_client.get("client_code", None)
                except Exception as client_error:
                    logger.error(f"Error fetching client info: {str(client_error)}")
                    # Don't fail authentication if client info can't be fetched
                    pass

            # Ensure role_name is always an array, even if stored as a single string
            role_name = found_user.get("role_name", "")
            if not role_name:
                role_name = found_user.get("role_names", {})
            
            # Ensure role_permissions is always a dictionary
            role_permissions = found_user.get("role_permissions", {})
            if not isinstance(role_permissions, dict):
                role_permissions = {}

            # Return user data
            return {
                "status": "success",
                "user_name": found_user["user_name"],
                "client_id": str(client_id) if client_id else None,
                "client_name": client_name,
                "client_code": client_code,
                "role_name": role_name,
                "role_permissions": role_permissions
            }
        except Exception as e:
            logger.error(f"Error in authenticate_user: {str(e)}")
            return None

    async def add_user(self, user_data):
        try:
            # Check if user already exists (case-insensitive search)
            existing_user = await self.db_users.find_one({
                "client_id": user_data.client_id,
                "user_name": {"$regex": f"^{user_data.user_name}$", "$options": "i"}
            })
            
            if existing_user:
                return {"status": "fail", "message": "Username already exists"}
            
            # Hash the password before storing it
            hashed_password = self.hash_password(user_data.password)
            
            new_user = {
                "user_name": user_data.user_name,
                "password": hashed_password,
                "client_id": user_data.client_id,
                "email": user_data.email,
                "is_system_generated": user_data.is_system_generated,
                "created_by": user_data.created_by,
                "created_dt": user_data.created_dt,
                "updated_by": user_data.updated_by,
                "updated_dt": user_data.updated_dt,
            }

            if hasattr(user_data, 'role'):
                new_user["role_permissions"] = user_data.role_permissions
                new_user["role_name"] = user_data.role_name
                new_user["role"] = user_data.role
            
            result = await self.db_users.insert_one(new_user)
            
            if self.db_logs is not None:
                await self.db_logs.insert_one({
                    "type": "user_created", 
                    "user": user_data.user_name,
                    "created_by": user_data.created_by,
                    "timestamp": datetime.utcnow()
                })
            
            return {"status": "success", "message": "User added successfully", "id": str(result.inserted_id)}
        
        except Exception as e:
            raise e

    async def get_users_by_client(self, client_id: str):
        try:
            # Find all users for the given client ID
            cursor = self.db_users.find({
                "client_id": client_id
            })
            
            users_list = []
            async for user in cursor:
                user["_id"] = str(user["_id"])
                users_list.append(user)

            if not users_list:
                return {"status": "fail", "message": "No users found for this client or only one user exists"}

            return {
                "status": "success",
                "message": "Users retrieved successfully (excluding first user)",
                "users": users_list
            }

        except Exception as e:
            raise e

    async def update_user(self, user_id: str, user_data: dict):
        try:
            if not ObjectId.is_valid(user_id):
                raise HTTPException(status_code=400, detail="Invalid user ID format")
                
            existing_user = await self.db_users.find_one({"_id": ObjectId(user_id)})
            if existing_user is None:
                raise HTTPException(status_code=404, detail="User not found")
                
            # If password is being updated, hash it
            if "password" in user_data:
                user_data["password"] = self.hash_password(user_data["password"])
                
            # Add updated timestamp
            user_data["updated_dt"] = datetime.utcnow()
            
            result = await self.db_users.update_one({"_id": ObjectId(user_id)}, {"$set": user_data})
            
            if self.db_logs:
                await self.db_logs.insert_one({
                    "type": "user_updated",
                    "user_id": user_id,
                    "updated_by": user_data.get("updated_by", "system"),
                    "timestamp": datetime.utcnow()
                })
            
            return {"status": "success", "message": "User updated successfully"} if result.modified_count > 0 else {"status": "success", "message": "No changes made"}
        except HTTPException as e:
            raise e
        except Exception as e:
            raise Exception(f"An error occurred while updating the user with ID {user_id}.")

    async def delete_user(self, user_id: str):
        try:
            if not ObjectId.is_valid(user_id):
                raise HTTPException(status_code=400, detail="Invalid user ID format")
                
            existing_user = await self.db_users.find_one({"_id": ObjectId(user_id)})
            if existing_user is None:
                raise HTTPException(status_code=404, detail="User not found")
                
            result = await self.db_users.delete_one({"_id": ObjectId(user_id)})
            
            if self.db_logs:
                await self.db_logs.insert_one({
                    "type": "user_deleted",
                    "user_id": user_id,
                    "timestamp": datetime.utcnow()
                })
            
            return {"status": "success", "message": "User deleted successfully"} if result.deleted_count > 0 else {"status": "success", "message": "No user deleted"}
        except HTTPException as e:
            raise e
        except Exception as e:
            raise Exception(f"An error occurred while deleting the user with ID {user_id}.")
    