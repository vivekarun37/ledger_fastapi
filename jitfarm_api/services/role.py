from bson import ObjectId
from fastapi import HTTPException
from pymongo.errors import PyMongoError
from datetime import datetime
from typing import Dict, List, Any

class RoleService:
    def __init__(self, db):
        self.db_roles = db.roles
        self.db = db

    def add_role(self, role_data: dict):
        try:
            # Ensure client_id is included in the role data
            if "client_id" not in role_data:
                raise HTTPException(status_code=400, detail="client_id is required")
                
            # Add timestamp data if not present
            if "created_dt" not in role_data:
                role_data["created_dt"] = datetime.utcnow()
                
            # Make sure we're using the correct database collection
            if not hasattr(self, 'db_roles') or self.db_roles is None:
                raise ValueError("Database collection 'db_roles' is not properly initialized")
                
            # Perform insertion
            result = self.db_roles.insert_one(role_data)
            
            # Safely handle the result
            if hasattr(result, 'inserted_id'):
                inserted_id = result.inserted_id
                print(f"Role added with ID: {inserted_id}")
                return str(inserted_id)
            else:
                # If result is a string or some other type without inserted_id
                print(f"Unexpected result type: {type(result)}")
                if isinstance(result, str):
                    return result  # Just return the string if that's what we got
                return str(result)  # Convert whatever we got to a string
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    def get_all_roles(self, client_id: str = None):
        try:
            # If client_id is provided, filter by it
            query = {"client_id": client_id} if client_id else {}
            
            roles = list(self.db_roles.find(query))
        
            
            for role in roles:
                role["_id"] = str(role["_id"])
            
            return roles
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    def get_role_by_id(self, role_id: str):
        try:
            if not ObjectId.is_valid(role_id):
                raise HTTPException(status_code=400, detail="Invalid role ID format")
                
            role = self.db_roles.find_one({"_id": ObjectId(role_id)})
            if role is None:  # Changed from 'if not role:'
                raise HTTPException(status_code=404, detail="Role not found")
                
            role["_id"] = str(role["_id"])
            return role
        except HTTPException as e:
            raise e
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    def update_role(self, role_id: str, role_data: dict):
        try:
            if not ObjectId.is_valid(role_id):
                raise HTTPException(status_code=400, detail="Invalid role ID format")

            existing_role = self.db_roles.find_one({"_id": ObjectId(role_id)})
            if existing_role is None:  # Changed from 'if not existing_role:'
                raise HTTPException(status_code=404, detail="Role not found")
                
            # Ensure client_id can't be changed
            if "client_id" in role_data and role_data["client_id"] != existing_role.get("client_id"):
                raise HTTPException(status_code=400, detail="client_id cannot be modified")
                
            # Add updated timestamp
            role_data["updated_dt"] = datetime.utcnow()

            result = self.db_roles.update_one({"_id": ObjectId(role_id)}, {"$set": role_data})

            users = self.db.users.find({"roles": role_id})
            for user in users:
                self.db.users.update_one(
                    {"_id": ObjectId(user["_id"])},
                    {"$set": {"role_permissions": role_data["permissions"]}}
                )
            return {"status": "success", "message": "Role updated successfully"} if result.modified_count > 0 else {"status": "success", "message": "No changes made"}
        except HTTPException as e:
            raise e
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    def delete_role(self, role_id: str):
        try:
            if not ObjectId.is_valid(role_id):
                raise HTTPException(status_code=400, detail="Invalid role ID format")
            
            role = self.db_roles.find_one({"_id": ObjectId(role_id)})
            if role is None:  # Changed from 'if not role:'
                raise HTTPException(status_code=404, detail="Role not found")
            
            result = self.db_roles.delete_one({"_id": ObjectId(role_id)})
            return {"status": "success", "message": "Role deleted successfully"} if result.deleted_count > 0 else {"status": "success", "message": "No role deleted"}
        except HTTPException as e:
            raise e
        except PyMongoError as e:
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    def get_all_permissions(self):
        try:
            permissions = self.db.permissions.find()
            permission_list = list(permissions)
            if not permission_list:
                return []
                
            for permission in permission_list:
                permission["_id"] = str(permission["_id"])
                
            return permission_list
        except Exception as e:
            # Log the actual exception for better debugging
            print(f"Error fetching permissions: {str(e)}")
            raise Exception(f"An error occurred while fetching permissions: {str(e)}")