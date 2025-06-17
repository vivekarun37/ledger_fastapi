from pymongo import MongoClient
from jitfarm_api.models.farmModel import Clients, Users
from bson import ObjectId
from fastapi import HTTPException, status
from jitfarm_api.services.user import UserService
from jitfarm_api.services.role import RoleService
from datetime import datetime
from pymongo.errors import PyMongoError
import json

class ClientService:
    def __init__(self, db):
        self.db = db
        self.user_service = UserService(self.db.users, self.db.clients, 
                                        self.db.logs if hasattr(self.db, 'logs') else None,
                                        self.db.error_log if hasattr(self.db, 'error_log') else None)
        self.role_service = RoleService(self.db)

    async def add_client(self, client_data: dict):
        try:
            result = await self.db.clients.insert_one(client_data)
            client_id = str(result.inserted_id)
            
            # Find existing users for this client
            existing_users = []
            async for user in self.db.users.find({"client_id": client_id}):
                existing_users.append(user)
            
            # Only create admin user if there are no users for this client yet
            if len(existing_users) == 0:
                client_code = client_data.get("client_code", "").strip() 
                if not client_code:
                    client_code = f"CLIENT{client_id[-4:]}"
                    
                # Create username and default password
                admin_username = f"{client_code}admin"
                default_password = "password"
                
                # Generate a default admin email
                admin_email = f"{admin_username}@{client_code.lower()}.com"
                
                # Create user object with email field
                admin_user = Users(
                    user_name=admin_username,
                    email=admin_email,
                    password=default_password,
                    client_id=client_id,
                    created_by=client_data.get("created_by", "system"),
                    created_dt=datetime.utcnow(),
                    updated_by=client_data.get("created_by", "system"),
                    updated_dt=datetime.utcnow()
                )
                
                # Add the user (use await since add_user is async)
                user_result = await self.user_service.add_user(admin_user)
                
                # Check if user was created successfully
                if user_result.get("status") and user_result["status"] != "success":
                    # Rollback client creation if user creation fails
                    await self.db.clients.delete_one({"_id": ObjectId(client_id)})
                    raise Exception(f"Failed to create admin user: {user_result.get('message')}")
                
                # 3. Create admin role with full permissions
                admin_role_data = {
                    "client_id": client_id,
                    "name": f"{client_code}admin",
                    "description": f"Administrator role for {client_data.get('name')}",
                    "is_system_generated": True,
                    "permissions": {
                        "Account": {
                            "read": True,
                            "create": True,
                            "update": True,
                            "delete": True
                        },
                        "Contacts": {
                            "read": True,
                            "create": True,
                            "update": True,
                            "delete": True
                        },
                        "Device": {
                            "read": True,
                            "create": True,
                            "update": True,
                            "delete": True
                        },
                        "Crop": {
                            "read": True,
                            "create": True,
                            "update": True,
                            "delete": True
                        },
                        "Field": {
                            "read": True,
                            "create": True,
                            "update": True,
                            "delete": True,
                            "Status Update": {
                                "read": True,
                                "create": True,
                                "update": True,
                                "delete": True
                            },
                            "Cost Update": {
                                "read": True,
                                "create": True,
                                "update": True,
                                "delete": True
                            }
                        },
                        "Users": {
                            "read": True,
                            "create": True,
                            "update": True,
                            "delete": True
                        },
                        "Roles": {
                            "read": True,
                            "create": True,
                            "update": True,
                            "delete": True
                        },
                        "Reports": {
                            "read": True,
                            "create": False,
                            "update": False,
                            "delete": False
                        },
                        "Data Addition": {
                            "read": True,
                            "create": True,
                            "update": True,
                            "delete": True
                        },
                    },
                    "created_by": client_data.get("created_by", "system"),
                    "created_dt": datetime.utcnow()
                }
                
                # Add the role - now using await since add_role is async
                try:
                    role_id = await self.role_service.add_role(admin_role_data)
                    await self.db.roles.update_one(
                        {"_id": ObjectId(role_id)},
                        {"$set": {
                            "is_system_generated": True,
                        }})
                    print(f"Created role with ID: {role_id} for client ID: {client_id}")
                    roles = await self.role_service.get_role_by_id(role_id)
                    # 4. Assign role to user
                    if roles.get("permissions") and roles.get("name"):
                        role_permissions = roles["permissions"]
                        role_name = roles["name"]
                    await self.db.users.update_one(
                        {"user_name": admin_username},
                        {
                            "$set": {
                                "is_system_generated": True,
                                "role_permissions": role_permissions,
                                "role_name": role_name
                            }
                        }
                    )
                except Exception as role_error:
                    print(f"Error creating role: {str(role_error)}")
                    # Rollback user creation if role creation fails
                    await self.db.users.delete_one({"user_name": admin_username})
                    # Rollback client creation
                    await self.db.clients.delete_one({"_id": ObjectId(client_id)})
                    raise Exception(f"Failed to create admin role: {str(role_error)}")
                
                return {
                    "client_id": client_id,
                    "admin_user_created": True,
                    "username": admin_username
                }
            else:
                # No admin user was created because users already exist
                return {
                    "client_id": client_id,
                    "admin_user_created": False
                }
            
        except Exception as e:
            # Log the error if you have a logging mechanism
            # Perform any necessary rollbacks
            raise Exception(f"An error occurred while adding the client and setting up admin access: {str(e)}")

    # Rest of the methods remain unchanged
    async def get_all_clients(self):
        try:
            clients = await self.db.clients.find().to_list(length=None)
            for client in clients:
                client["_id"] = str(client["_id"])
            return clients
        except Exception as e:
            raise Exception("An error occurred while fetching clients.") from e

    async def get_client_by_id(self, client_id: str):
        try:
            if not ObjectId.is_valid(client_id):
                raise HTTPException(status_code=400, detail="Invalid client ID format")
                
            client = await self.db.clients.find_one({"_id": ObjectId(client_id)})
            if client is None:  # Changed from 'if not client:'
                raise HTTPException(status_code=404, detail="Client not found")
                
            client["_id"] = str(client["_id"])
            return client
        except HTTPException as e:
            raise e
        except Exception as e:
            raise Exception(f"An error occurred while fetching the client with ID {client_id}.") from e

    async def update_client(self, client_id: str, client):
        try:
            if not ObjectId.is_valid(client_id):
                raise HTTPException(status_code=400, detail="Invalid client ID format")

            existing_client = await self.db.clients.find_one({"_id": ObjectId(client_id)})
            if existing_client is None:
                raise HTTPException(status_code=404, detail="Client not found")

            update_data = {
                "name": client.name,
                "description": client.description,
                "updated_dt": client.updated_dt or datetime.utcnow(),
                "updated_by": client.updated_by,
            }
            
            result = await self.db.clients.update_one({"_id": ObjectId(client_id)}, {"$set": update_data})
            return {"message": "Client updated successfully"} if result.modified_count > 0 else {"message": "No changes made"}
        except HTTPException as e:
            raise e
        except Exception as e:
            raise Exception(f"An error occurred while updating the client with ID {client_id}.") from e

    async def delete_client(self, client_id: str):
        try:
            if not ObjectId.is_valid(client_id):
                raise HTTPException(status_code=400, detail="Invalid client ID format")
            
            client = await self.db.clients.find_one({"_id": ObjectId(client_id)})
            if client is None:  # Changed from 'if not client:'
                raise HTTPException(status_code=404, detail="Client not found")
            
            deletion_results = {}
            
            user_result = await self.db.users.delete_many({"client_id": client_id})
            deletion_results["users"] = user_result.deleted_count
            role_result = await self.db.roles.delete_many({"client_id": client_id})
            deletion_results["roles"] = role_result.deleted_count
            result = await self.db.clients.delete_one({"_id": ObjectId(client_id)})
            deletion_results["clients"] = result.deleted_count
            
            return {
                "message": "Client, users, and roles deleted successfully",
                "deleted_counts": deletion_results
            } if result.deleted_count > 0 else {"message": "No client deleted"}
        except HTTPException as e:
            raise e
        except Exception as e:
            raise Exception(f"An error occurred while deleting the client with ID {client_id}.") from e