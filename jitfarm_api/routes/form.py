from fastapi import APIRouter, Depends, Request, Body, Query, HTTPException
from models.farmModel import Form, Field
from services.form import FormService
from typing import Dict, List, Optional
import json
from datetime import datetime
from pydantic import BaseModel

form_router = APIRouter(prefix="", tags=['Form'])

from utils import log_error,get_current_user,permission_required

def get_form_service(request: Request) -> FormService:
    return FormService(request.app)

@form_router.delete("/deleteform")
async def delete_form(
    request: Request,
    _id: str,
    form_service: FormService = Depends(get_form_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Data Addition", "delete"))
):
    try:
        if permission:
            return await form_service.delete_form(_id)
        else:
            log_error(request.app, request, "Permission denied for delete_form", None, {"form_id": _id})
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to delete forms"
            )
    except ValueError as e:
        return {"status": "fail", "message": str(e)}
    except Exception as e:
        # Log the error
        db = request.app.state.db if hasattr(request.app.state, 'db') else None
        log_error(
            db=db,
            request=request,
            error_message=f"Error deleting form with ID {_id}",
            exception=e,
            payload=json.dumps({"form_id": _id})
        )
        return {"status": "error", "message": f"An error occurred while deleting the form"}

@form_router.delete("/deleteformdata")
async def delete_form_data(
    request: Request,
    _id: str,
    form_service: FormService = Depends(get_form_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Data Addition", "update"))
):
    try:
        return await form_service.delete_form_data(_id)
    except ValueError as e:
        return {"status": "fail", "message": str(e)}
    except Exception as e:
        db = request.app.state.db if hasattr(request.app.state, 'db') else None
        log_error(
            db=db,
            request=request,
            error_message=f"Error deleting form data with ID {_id}",
            exception=e,
            payload=json.dumps({"form_data_id": _id})
        )
        return {"status": "error", "message": f"An error occurred while deleting the form data"}

@form_router.get("/getform")
async def get_form(
    request: Request,
    stage: str = Query(..., description="Stage of the form to retrieve"),
    client_id: Optional[str] = Query(None, description="Client ID to filter forms"),
    form_service: FormService = Depends(get_form_service)
):
    try:
        return await form_service.get_form(stage, client_id)
    except Exception as e:
        # Log the error
        db = request.app.state.db if hasattr(request.app.state, 'db') else None
        log_error(
            db=db,
            request=request,
            error_message=f"Error retrieving form for stage {stage}",
            exception=e,
            payload=json.dumps({"stage": stage, "client_id": client_id})
        )
        return {"status": "error", "message": f"An error occurred while retrieving the form"}

@form_router.post("/addformData")
async def add_form_data(
    request: Request,
    form_service: FormService = Depends(get_form_service)
):
    try:
        data = await request.json()
        
        # Validate required fields according to Form model
        required_fields = {"client_id", "stage", "fields", "created_by", "updated_by"}
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            return {"status": "fail", "message": f"Missing required fields: {missing_fields}"}
        
        # Set creation and update timestamps if not provided
        if "created_dt" not in data:
            data["created_dt"] = datetime.utcnow().isoformat()
        if "updated_dt" not in data:
            data["updated_dt"] = datetime.utcnow().isoformat()
            
        return await form_service.add_form_data(data)
    except ValueError as e:
        # Client error - validation failed
        return {"status": "fail", "message": str(e)}
    except Exception as e:
        # Log the error
        db = request.app.state.db if hasattr(request.app.state, 'db') else None
        # Create a safe payload that excludes potentially sensitive field values
        safe_payload = {}
        if isinstance(data, dict):
            safe_payload = {
                "stage": data.get("stage"),
                "client_id": data.get("client_id"),
                "created_by": data.get("created_by"),
                "field_count": len(data.get("fields", {})) if isinstance(data.get("fields"), dict) else "unknown"
            }
        
        log_error(
            db=db,
            request=request,
            error_message="Error adding form data",
            exception=e,
            payload=json.dumps(safe_payload)
        )
        return {"status": "error", "message": "An error occurred while saving form data"}

@form_router.put("/updateformData")
async def update_form_data(
    request: Request,
    form_service: FormService = Depends(get_form_service)
):
    try:
        data = await request.json()
        
        if "_id" not in data:
            return {"status": "fail", "message": "Form ID is required for update"}
        
        # Always update the updated_dt timestamp
        data["updated_dt"] = datetime.utcnow().isoformat()
        
        return await form_service.update_form_data(data)
    except ValueError as e:
        # Client error - validation failed
        return {"status": "fail", "message": str(e)}
    except Exception as e:
        # Log the error
        db = request.app.state.db if hasattr(request.app.state, 'db') else None
        safe_payload = {}
        if isinstance(data, dict):
            safe_payload = {
                "form_id": str(data.get("_id", "")),
                "stage": data.get("stage"),
                "client_id": data.get("client_id"),
                "updated_by": data.get("updated_by"),
                "field_count": len(data.get("fields", {})) if isinstance(data.get("fields"), dict) else "unknown"
            }
        
        log_error(
            db=db,
            request=request,
            error_message="Error updating form data",
            exception=e,
            payload=json.dumps(safe_payload)
        )
        return {"status": "error", "message": "An error occurred while updating form data"}

@form_router.get("/getFormData/")
async def get_form_data(
    request: Request,
    stage: Optional[str] = Query(None, description="Filter by stage"),
    client_id: Optional[str] = Query(None, description="Filter by client ID"),
    created_by: Optional[str] = Query(None, description="Filter by creator"),
    limit: int = Query(10, description="Number of records to retrieve (default: 10)"),
    offset: int = Query(0, description="Number of records to skip (default: 0)"),
    form_service: FormService = Depends(get_form_service)
):
    try:
        return await form_service.get_form_data(stage, client_id, created_by, limit, offset)
    except Exception as e:
        # Log the error
        db = request.app.state.db if hasattr(request.app.state, 'db') else None
        log_error(
            db=db,
            request=request,
            error_message="Error retrieving form data",
            exception=e,
            payload=json.dumps({
                "stage": stage,
                "client_id": client_id,
                "created_by": created_by,
                "limit": limit,
                "offset": offset
            })
        )
        return {"status": "error", "message": "An error occurred while retrieving form data"}

@form_router.get("/getFormsByClient")
async def get_forms_by_client(
    request: Request,
    client_id: str = Query(..., description="Client ID to filter forms"),
    form_service: FormService = Depends(get_form_service)
):
    try:
        return await form_service.get_forms_by_client(client_id)
    except Exception as e:
        # Log the error
        db = request.app.state.db if hasattr(request.app.state, 'db') else None
        log_error(
            db=db,
            request=request,
            error_message=f"Error retrieving forms for client {client_id}",
            exception=e,
            payload=json.dumps({"client_id": client_id})
        )
        return {"status": "error", "message": f"An error occurred while retrieving forms for the client"}

@form_router.get("/getstages")
async def get_stages(
    request: Request,
    client_id: Optional[str] = Query(None, description="Client ID to filter stages"),
    form_service: FormService = Depends(get_form_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Data Addition", "read"))
):
    try:
        if not permission:
            log_error(request.app, request, "Permission denied for get_stages", None, json.dumps({"client_id": client_id}) if client_id else {})
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to get stages"
            )
            
        return await form_service.get_stages(client_id)
            
    except HTTPException:
        # Re-raise HTTPExceptions (like the 403 we raised above)
        raise
    except Exception as e:
        # Log and handle other unexpected errors
        db = request.app.state.db if hasattr(request.app.state, 'db') else None
        log_error(
            db=db,
            request=request,
            error_message="Error retrieving form stages",
            exception=e,
            payload=json.dumps({"client_id": client_id}) if client_id else {}
        )
        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving form stages"
        )