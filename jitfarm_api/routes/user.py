import bcrypt
from fastapi import APIRouter, Depends, Request, Body, Query, HTTPException, status
from models.farmModel import Users, UserLogin
from bson import ObjectId
from pymongo import MongoClient
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from services.user import UserService
import json
from utils import log_error,get_current_user,permission_required
import traceback

user_router = APIRouter(prefix="", tags=['User'])

def get_user_service(request: Request) -> UserService:
    db_users = request.app.users
    db_clients = request.app.clients
    db_logs = request.app.logs if hasattr(request.app, 'logs') else None
    db_error_log = request.app.error_log if hasattr(request.app, 'error_log') else None
    
    return UserService(db_users, db_clients, db_logs, db_error_log)

@user_router.post("/getusers",summary="User Login")
async def get_users(request: Request, data: UserLogin):
    user_service = get_user_service(request)
    user_name = data.user_name
    password = data.password
    
    if not user_name or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")
    
    try:
        result = await user_service.authenticate_user(user_name, password)
        print(f"Authentication result: {result}")
        
        if result.get("status") == "fail":
            return JSONResponse(
                content=result,
                status_code=401 if "Invalid username or password" in result.get("message", "") else 400
            )
        
        return JSONResponse(content=result)
    except Exception as e:
        print(f"Error in get_users: {str(e)}")
        print(traceback.format_exc())
        db = request.app.state.db if hasattr(request.app.state, 'db') else None
        log_error(
            db=db,
            request=request,
            error_message="Error during user authentication",
            exception=e,
            payload=json.dumps({"user_name": user_name})  # Don't include password in logs
        )
        
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500
        )

@user_router.post("/adduser")
async def add_user(request: Request, user: Users,
 user_service: UserService = Depends(get_user_service),
 users: dict = Depends(get_current_user),
 permission: bool = Depends(permission_required("Users", "create"))):

    try:
        if permission:
            result = await user_service.add_user(user)
            if result.get("status") == "fail":
                return JSONResponse(
                    content=result,
                    status_code=400
                )
            
            return JSONResponse(
                content=result,
                status_code=201
            )
        else:
            log_error(
                request.app,
                request,
                error_message="Permission denied for add_user",
                exception=None,
                payload=json.dumps(user.dict())
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to add users"
            )
    except Exception as e:
        db = request.app.state.db if hasattr(request.app.state, 'db') else None
        safe_payload = {
            "user_name": user.user_name,
            "client_id": user.client_id,
        }
        
        log_error(
            request.app,
            request,
            error_message="Error adding new user",
            exception=e,
            payload=json.dumps(safe_payload)
        )
        
        return JSONResponse(
            content={"status": "error", "message": "Error occurred while adding user"},
            status_code=500
        )

@user_router.get("/get_users_by_client/{client_id}")
async def get_users_by_client_get(request: Request, client_id: str, user_service: UserService = Depends(get_user_service),
 user: dict = Depends(get_current_user), permission: bool = Depends(permission_required("Users", "read"))):
    
    try:     
        if permission:                   
            result = await user_service.get_users_by_client(client_id)
            if result.get("status") == "fail":
                return JSONResponse(
                    content=result,
                    status_code=400
                )
            
            # Convert datetime objects to ISO format strings
            if "users" in result:
                for user in result["users"]:
                    if "created_dt" in user and isinstance(user["created_dt"], datetime):
                        user["created_dt"] = user["created_dt"].isoformat()
                    if "updated_dt" in user and isinstance(user["updated_dt"], datetime):
                        user["updated_dt"] = user["updated_dt"].isoformat()
            
            return JSONResponse(content=result)
        else:
            log_error(
                request.app,
                request,
                error_message="Permission denied for get_users_by_client",
                exception=None,
                payload=json.dumps({"client_id": client_id})
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view users"
            )
    except Exception as e:
        # Using the format you provided
        log_error(
            request.app, 
            request, 
            "Error fetching users by client", 
            e, 
            json.dumps({"client_id": client_id})
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@user_router.put("/update_user/{user_id}")
async def update_user(request: Request, user_id: str, 
user_data: dict = Body(...),
 user_service: UserService = Depends(get_user_service),
 user: dict = Depends(get_current_user), permission: bool = Depends(permission_required("Users", "update"))):
    
    try:
        if permission:
            result = await user_service.update_user(user_id, user_data)
            
            if result.get("status") == "fail":
                return JSONResponse(
                    content=result,
                    status_code=400
                )
            
            return JSONResponse(content=result)
        else:
            log_error(
                request.app,
                request,
                error_message="Permission denied for update_user",
                exception=None,
                payload=json.dumps({"user_id": user_id, **user_data})
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update users"
            )
    except Exception as e:
        safe_data = {k: v for k, v in user_data.items() if k != "password"}
        
        db = request.app.state.db if hasattr(request.app.state, 'db') else None
        log_error(
            db=db,
            request=request,
            error_message="Error updating user",
            exception=e,
            payload=json.dumps({"user_id": user_id, **safe_data})
        )
        
        return JSONResponse(
            content={"status": "error", "message": "Error occurred while updating user"},
            status_code=500
        )

@user_router.delete("/delete_user")
async def delete_user(request: Request, user_id: str = Query(...),
 user_service: UserService = Depends(get_user_service),
 user: dict = Depends(get_current_user), permission: bool = Depends(permission_required("Users", "delete"))):

    
    try:
        if permission:
            result = await user_service.delete_user(user_id)
            
            if result.get("status") == "fail":
                return JSONResponse(
                    content=result,
                    status_code=400
                )
            
            return JSONResponse(content=result)
        else:
            log_error(
                request.app,
                request,
                error_message="Permission denied for delete_user",
                exception=None,
                payload=json.dumps({"user_id": user_id})
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete users"
            )
    except Exception as e:
        db = request.app.state.db if hasattr(request.app.state, 'db') else None
        log_error(
            db=db,
            request=request,
            error_message="Error deleting user",
            exception=e,
            payload=json.dumps({"user_id": user_id})
        )
        
        return JSONResponse(
            content={"status": "error", "message": "Error occurred while deleting user"},
            status_code=500
        )

@user_router.post("/create_first_user")
async def create_first_user(request: Request, user: Users, user_service: UserService = Depends(get_user_service)):
    try:
        # Check if any users exist
        users_count = request.app.users.count_documents({})
        if users_count > 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot create first user - users already exist"
            )
        
        # Add admin role permissions
        user.role_permissions = {
            "Users": {"create": True, "read": True, "update": True, "delete": True},
            "Account": {"create": True, "read": True, "update": True, "delete": True, "COA": {"create": True, "read": True, "update": True, "delete": True}},
            "Clients": {"create": True, "read": True, "update": True, "delete": True},
            "Roles": {"create": True, "read": True, "update": True, "delete": True}
        }
        user.role_name = "admin"
        
        result = await user_service.add_user(user)
        return JSONResponse(content=result, status_code=201)
        
    except Exception as e:
        log_error(
            request.app,
            request,
            error_message="Error creating first user",
            exception=e,
            payload=json.dumps({"user_name": user.user_name})
        )
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )