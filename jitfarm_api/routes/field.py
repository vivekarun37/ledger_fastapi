from fastapi import APIRouter, Depends, Request, Body, Query, HTTPException
from jitfarm_api.models.farmModel import Fields
from jitfarm_api.services.field import FieldService
from typing import Dict, List, Optional
import json
from jitfarm_api.utils import log_error, get_current_user, permission_required, additional_permissions_required

field_router = APIRouter(prefix="", tags=['Field'])

def get_field_service(request: Request) -> FieldService:
    return FieldService(request.app)

@field_router.post("/add_field")
async def add_field(
    request: Request,
    field: Fields,
    field_service: FieldService = Depends(get_field_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Field", "create"))
):
    if permission:
        result, exception = await field_service.add_field(field)
    else:
        log_error(request.app, request, "Permission denied for add_field", None, field.dict())
        raise HTTPException(status_code=403, detail="You don't have permission to add fields")
    if exception:
        log_error(request.app, request, "Failed to add field", exception, str(field))
        status_code = 500 if isinstance(exception, Exception) else 400
        raise HTTPException(status_code=status_code, detail=result["message"])
    return result

@field_router.get("/get_fields")
async def get_fields(
    request: Request,
    client_id: str,
    field_service: FieldService = Depends(get_field_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Field", "read"))
):
    if permission:
        fields, exception = await field_service.get_fields(client_id)
    else:
        log_error(request.app, request, "Permission denied for get_fields", None, {"client_id": client_id})
        raise HTTPException(status_code=403, detail="You don't have permission to get fields")
    if exception:
        # Log error and return appropriate HTTP status
        log_error(request.app, request, f"Failed to retrieve fields for client {client_id}", exception)
        raise HTTPException(status_code=500, detail=f"Error retrieving fields: {str(exception)}")
    return fields

@field_router.put("/update_field/{field_id}")
async def update_field(
    request: Request,
    field_id: str,
    field: dict = Body(...),
    field_service: FieldService = Depends(get_field_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Field", "update"))
):
    if permission:
        result, exception = await field_service.update_field(field_id, field)
    else:
        log_error(request.app, request, "Permission denied for update_field", None, str(field))
        raise HTTPException(status_code=403, detail="You don't have permission to update fields")
    if exception:
        status_code = 400 if isinstance(exception, ValueError) else 500
        error_message = result["message"]
        log_error(request.app, request, f"Error updating field {field_id}", exception, str(field))
        raise HTTPException(status_code=status_code, detail=error_message)
    
    return result
    
@field_router.put("/update_field_devices/{field_id}")
async def update_field_devices(
    request: Request,
    field_id: str,
    device_data: dict = Body(...),
    field_service: FieldService = Depends(get_field_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Field", "update"))
):
    if permission:
        result, exception = await field_service.update_field_devices(field_id, device_data)
    else:
        log_error(request.app, request, "Permission denied for update_field_devices", None, str(device_data))
        raise HTTPException(status_code=403, detail="You don't have permission to update field devices")
    if exception:
        status_code = 400 if isinstance(exception, ValueError) else 500
        error_message = result["message"]
        log_error(request.app, request, f"Failed to update devices for field {field_id}", exception, str(device_data))
        raise HTTPException(status_code=status_code, detail=error_message)
        
    return result

@field_router.delete("/delete_field")
async def delete_field(
    request: Request,
    field_id: str = Query(...),
    field_service: FieldService = Depends(get_field_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Field", "delete"))
):
    if permission:
        result, exception = await field_service.delete_field(field_id)
    else:
        log_error(request.app, request, "Permission denied for delete_field", None, {"field_id": field_id})
        raise HTTPException(status_code=403, detail="You don't have permission to delete fields")
    if exception:
        status_code = 400 if isinstance(exception, ValueError) else 500
        error_message = result["message"]
        log_error(request.app, request, f"Error deleting field {field_id}", exception)
        raise HTTPException(status_code=status_code, detail=error_message)
    
    return result

@field_router.put("/update_task_status/{field_id}")
async def update_task_status(
    request: Request,
    field_id: str,
    task_data: dict = Body(...),
    field_service: FieldService = Depends(get_field_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Field", "update")),
    additional_permission: bool = Depends(additional_permissions_required("Field","Status Update", "update"))

):
    
    if permission or additional_permission:
        task_id = task_data.get("task_id")
        new_status = task_data.get("new_status")
        crop_id = task_data.get("crop_id")
        
        if not task_id:
            raise HTTPException(
                status_code=400, 
                detail="task_id must be provided"
            )
        
        # Call specialized method to update just the task status
        result, exception = await field_service.update_task_status(field_id, task_id, new_status, crop_id)
    else:
        log_error(request.app, request, "Permission denied for update_task_status", None, str(task_data))
        raise HTTPException(status_code=403, detail="You don't have permission to update task status")
    
    if exception:
        status_code = 400
        error_message = result["message"]
        log_error(
            request.app, 
            request, 
            f"Failed to update task status for task {task_id} in field {field_id}: {error_message}", 
            exception,
            str(task_data)
        )
        raise HTTPException(status_code=status_code, detail=error_message)
        
    return result   

@field_router.put("/update_task_cost/{field_id}")
async def update_task_cost(
    request: Request,
    field_id: str,
    task_data: dict = Body(...),
    field_service: FieldService = Depends(get_field_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Field", "update")),
    additional_permission: bool = Depends(additional_permissions_required("Field", "Cost Update", "update"))
):
    try:
        if permission or additional_permission:
            # Validate required fields
            task_id = task_data.get("task_id")
            cost = task_data.get("cost")
            crop_id = task_data.get("crop_id")
            description = task_data.get("description", "Fertilizer cost")
            
            print(f"Received task data: {json.dumps(task_data, indent=2)}")
            print(f"Field ID: {field_id}")
            print(f"Task ID: {task_id}")
            print(f"Cost: {cost}")
            print(f"Crop ID: {crop_id}")
            
            if not task_id:
                raise HTTPException(status_code=400, detail="task_id must be provided")
            if cost is None:
                raise HTTPException(status_code=400, detail="cost must be provided")
            if not crop_id:
                raise HTTPException(status_code=400, detail="crop_id must be provided")
                
            result, exception = await field_service.update_task_cost(
                field_id, 
                task_id, 
                float(cost), 
                crop_id,
                description,
                user.get("user_name", "system")
            )
            
            if exception:
                status_code = 400 if isinstance(exception, ValueError) else 500
                error_message = result.get("message", str(exception))
                print(f"Error updating task cost: {error_message}")
                log_error(
                    request.app.db,
                    request,
                    f"Failed to update task cost for task {task_id} in field {field_id}: {error_message}",
                    exception,
                    str(task_data)
                )
                raise HTTPException(status_code=status_code, detail=error_message)
                
            return result
        else:
            error_msg = "You don't have permission to update task cost"
            print(f"Permission denied: {error_msg}")
            log_error(request.app.db, request, error_msg, None, str(task_data))
            raise HTTPException(status_code=403, detail=error_msg)
    except HTTPException as e:
        raise e
    except Exception as e:
        error_msg = f"Unexpected error updating task cost for field {field_id}, task {task_data.get('task_id')}: {str(e)}"
        print(f"Error: {error_msg}")
        log_error(request.app.db, request, error_msg, e, str(task_data))
        raise HTTPException(status_code=500, detail=error_msg)   