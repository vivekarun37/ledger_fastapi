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
        # Use a simple MD5 hash for testing
        hashed = hashlib.md5(password.encode()).hexdigest()
        logger.info(f"Hashing password: result={hashed}")
        return hashed

    def verify_password(self, password: str, hashed_password: str) -> bool:
        computed_hash = self.hash_password(password)
        logger.info(f"Verifying password: stored={hashed_password}, computed={computed_hash}")
        return computed_hash == hashed_password

    async def authenticate_user(self, user_name: str, password: str):
        try:
            logger.info(f"Authenticating user: {user_name}")
            if not user_name or not password:
                logger.warning("Username or password is empty")
                return {"status": "fail", "message": "Username and password are required"}

            # Use exact match with case-insensitive collation instead of regex
            try:
                found_user = await self.db_users.find_one(
                    {"user_name": user_name},
                    collation={"locale": "en", "strength": 2}  # Case-insensitive
                )
                logger.info(f"Found user: {found_user}")
            except Exception as db_error:
                logger.error(f"Database error: {str(db_error)}")
                raise Exception(f"Database error: {str(db_error)}")
            
            if not found_user:
                logger.warning("User not found")
                return {"status": "fail", "message": "Invalid username or password"}
                
            if not self.verify_password(password, found_user["password"]):
                logger.warning("Password verification failed")
                return {"status": "fail", "message": "Invalid username or password"}
        
            logger.info("User authenticated successfully")
            
            # Get client information if available
            client_id = found_user.get("client_id", None)
            client_name = None
            client_code = None
            if client_id:
                try:
                    # Ensure client_id is an ObjectId if it's a string
                    if isinstance(client_id, str):
                        client_id = ObjectId(client_id)
                    find_client = await self.db_clients.find_one({"_id": client_id})
                    client_name = find_client.get("name", None) if find_client else None
                    client_code = find_client.get("client_code", None) if find_client else None
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

            # Ensure client_id is serializable for JWT
            safe_client_id = str(client_id) if client_id else None

            try:
                access_token = create_access_token(
                    user_data={"user_name": found_user["user_name"], "client_id": safe_client_id, "permissions": role_permissions},
                    expiry=timedelta(minutes=300)
                )
                
                refresh_token = create_access_token(
                    user_data={"user_name": found_user["user_name"], "client_id": safe_client_id, "permissions": role_permissions},
                    expiry=timedelta(days=7),
                    refresh=True
                )
            except Exception as token_error:
                logger.error(f"Error creating tokens: {str(token_error)}")
                raise Exception(f"Error creating authentication tokens: {str(token_error)}")
            
            return {
                "status": "success",
                "message": "Valid user",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "client_name": client_name,
                "client_code": client_code,
                "user": {
                    "user_name": found_user["user_name"],
                    "client_id": safe_client_id,
                    "role_name": role_name,
                    "role_permissions": role_permissions,
                }
            }
        
        except Exception as e:
            logger.error(f"Error in authenticate_user: {str(e)}")
            logger.error(traceback.format_exc())
            raise e

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

            if user_data.role:
                new_user["role_permissions"] = user_data.role_permissions
                new_user["role_name"] = user_data.role_name
                new_user["role"] = user_data.role
            
            result = await self.db_users.insert_one(new_user)
            
            if self.db_logs:
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
            # Validate user_id format
            if not ObjectId.is_valid(user_id):
                return {"status": "fail", "message": "Invalid user ID format"}
                
            # Get the existing user
            existing_user = await self.db_users.find_one({"_id": ObjectId(user_id)})
            if not existing_user:
                return {"status": "fail", "message": "User not found"}
                
            # Prepare update data
            update_data = {k: v for k, v in user_data.items() if k != "_id"}
            
            # If updating password, hash it
            if "password" in update_data and update_data["password"]:
                update_data["password"] = self.hash_password(update_data["password"])
            else:
                # Don't update password if not provided
                update_data.pop("password", None)
                
            # Update user
            result = await self.db_users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                return {"status": "fail", "message": "No changes made"}
                
            # Log the update if logging is enabled
            if self.db_logs:
                await self.db_logs.insert_one({
                    "type": "user_updated", 
                    "user_id": user_id,
                    "updated_by": user_data.get("updated_by", "system"),
                    "timestamp": datetime.utcnow()
                })
                
            return {"status": "success", "message": "User updated successfully"}
        
        except Exception as e:
            # Propagate exception to route handler
            raise e

    async def delete_user(self, user_id: str):
        try:
            # Validate user_id format
            if not ObjectId.is_valid(user_id):
                return {"status": "fail", "message": "Invalid user ID format"}
                
            # Find and delete the user
            result = await self.db_users.delete_one({"_id": ObjectId(user_id)})
            
            if result.deleted_count == 0:
                return {"status": "fail", "message": "User not found"}
                
            return {"status": "success", "message": "User deleted successfully"}
        
        except Exception as e:
            raise e
    