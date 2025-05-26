from fastapi import APIRouter, Request, HTTPException, status, Depends
from models.farmModel import Clients
from services.client import ClientService
import json
from utils import log_error,get_current_user,permission_required


client_router = APIRouter(prefix="", tags=['Client'])

@client_router.post("/addclient")
async def add_client_route(request: Request, client: Clients, user: dict = Depends(get_current_user), permission: bool = Depends(permission_required("Clients", "create"))):
    try:
        if permission:
            db = type('DB', (), {})()
            db.clients = request.app.clients
            db.users = request.app.users
            db.roles = request.app.roles
            
            # If log collections are used in the service
            if hasattr(request.app, 'logs'):
                db.logs = request.app.logs
            if hasattr(request.app, 'error_log'):
                db.error_log = request.app.error_log
                
            client_service = ClientService(db)
            client_data = client.dict()
            
            # Add await here
            result = await client_service.add_client(client_data)
            
            # Check if admin user was created
            if result.get("admin_user_created", False):
                return {
                    "status": "success", 
                    "message": f"Client added successfully with admin user (username: {result.get('username')})", 
                    "id": result.get("client_id"),
                    "admin_created": True,
                    "admin_username": result.get("username")
                }
            else:
                return {
                    "status": "success", 
                    "message": "Client added successfully", 
                    "id": result.get("client_id"),
                    "admin_created": False
                }
        else:
            log_error(request.app, request, "Permission denied for add_client_route", None, json.dumps(client.dict(), default=str))
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to add clients")
    except Exception as e:
        log_error(request.app, request, "Error in add_client_route", e, json.dumps(client.dict(), default=str))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@client_router.get("/get_clients")
async def get_clients_route(request: Request, user: dict = Depends(get_current_user), permission: bool = Depends(permission_required("Clients", "read"))):
    try:
        if permission:
            db = request.app
            client_service = ClientService(db)
            return client_service.get_all_clients()
        else:
            log_error(request.app, request, "Permission denied for get_clients_route", None)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to get clients")
    except Exception as e:
        log_error(request.app, request, "Error in get_clients_route", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@client_router.put("/update_client/{client_id}")
async def update_client_route(request: Request, client_id: str, client: Clients, user: dict = Depends(get_current_user), permission: bool = Depends(permission_required("Clients", "update"))):
    try:
        if permission:
            db = request.app
            client_service = ClientService(db)
            return client_service.update_client(client_id, client)
        else:
            log_error(request.app, request, "Permission denied for update_client_route", None, client.dict())
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to update clients")
    except Exception as e:
        log_error(request.app, request, f"Error in update_client_route for client {client_id}", e, client.dict())
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@client_router.delete("/delete_client/{client_id}")
async def delete_client_route(request: Request, client_id: str, user: dict = Depends(get_current_user), permission: bool = Depends(permission_required("Clients", "delete"))):
    try:
        if permission:
            db = request.app
            client_service = ClientService(db)
            return client_service.delete_client(client_id)
        else:
            log_error(request.app, request, "Permission denied for delete_client_route", None, {"client_id": client_id})
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to delete clients")
    except Exception as e:
        log_error(request.app, request, f"Error in delete_client_route for client {client_id}", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
