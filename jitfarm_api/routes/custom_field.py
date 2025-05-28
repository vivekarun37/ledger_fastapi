from fastapi import APIRouter, Depends, Request, Body, Query, HTTPException
from jitfarm_api.models.farmModel import FieldTemplate
from jitfarm_api.services.custom_field import FieldTemplateService
from typing import List, Optional
from jitfarm_api.utils import log_error, get_current_user, permission_required 

field_template_router = APIRouter(prefix="", tags=['FieldTemplate'])

def get_field_template_service(request: Request) -> FieldTemplateService:
    return FieldTemplateService(request.app.db)

@field_template_router.get("/field_templates")
async def get_field_templates(
    request: Request,
    client_id: str = Query(..., description="Client ID"),
    applies_to: Optional[str] = None,
    field_template_service: FieldTemplateService = Depends(get_field_template_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Field", "read")) or Depends(permission_required("Crop", "read"))
):
    """Get all active field templates for a specific client"""
    try:
        if permission:
            return await field_template_service.get_field_templates(client_id, applies_to)
        else:
            log_error(request.app.db, request, "Permission denied for get_field_templates", None, {"client_id": client_id, "applies_to": applies_to})
            raise HTTPException(status_code=403, detail="Permission denied")
    except Exception as e:
        log_error(request.app.db, request, "Error getting field templates", e, '')
        raise HTTPException(status_code=500, detail=f"Error retrieving field templates: {str(e)}")

@field_template_router.get("/field_templates/{template_id}")
async def get_field_template(
    request: Request,
    template_id: str,
    field_template_service: FieldTemplateService = Depends(get_field_template_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Field", "read")) or Depends(permission_required("Crop", "read"))
):
    """Get a specific field template by ID"""
    try:
        if permission:
            return await field_template_service.get_field_template(template_id)
        else:
            log_error(request.app.db, request, "Permission denied for get_field_template", None, {"template_id": template_id})
            raise HTTPException(status_code=403, detail="Permission denied")
    except HTTPException as he:
        raise he
    except Exception as e:
        log_error(request.app.db, request, "Error getting field template", e, '')
        raise HTTPException(status_code=500, detail=f"Error retrieving field template: {str(e)}")

@field_template_router.post("/field_templates")
async def create_field_templates(
    request: Request,
    templates: List[FieldTemplate],
    client_id: str = Query(..., description="Client ID"),
    field_template_service: FieldTemplateService = Depends(get_field_template_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Field", "update")) or Depends(permission_required("Crop", "update"))
):
    try:
        if permission:
            return await field_template_service.create_field_templates(client_id, templates)
        else:
            log_error(request.app.db, request, "Permission denied for create_field_templates", None, {"client_id": client_id})
            raise HTTPException(status_code=403, detail="Permission denied")
    except Exception as e:
        log_error(request.app.db, request, "Error creating field templates", e, '')
        raise HTTPException(status_code=500, detail=f"Error creating field templates: {str(e)}")

# Add a PUT endpoint for entire collection updates
@field_template_router.put("/field_templates")
async def update_field_templates(
    request: Request,
    client_id: str = Query(..., description="Client ID"),
    templates: List[dict] = Body(...),
    field_template_service: FieldTemplateService = Depends(get_field_template_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Field", "update")) or Depends(permission_required("Crop", "update"))
):
    try:
        if permission:
            return await field_template_service.create_field_templates(client_id, [FieldTemplate(**template) for template in templates])
        else:
            log_error(request.app.db, request, "Permission denied for update_field_templates", None, {"client_id": client_id})
            raise HTTPException(status_code=403, detail="Permission denied")
    except Exception as e:
        log_error(request.app.db, request, "Error updating field templates", e, '')
        raise HTTPException(status_code=500, detail=f"Error updating field templates: {str(e)}")

@field_template_router.put("/field_templates/{template_id}")
async def update_field_template(
    request: Request,
    template_id: str,
    client_id: str = Query(..., description="Client ID"),
    template: dict = Body(...),
    field_template_service: FieldTemplateService = Depends(get_field_template_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Field", "update")) or Depends(permission_required("Crop", "update"))
):
    try:
        if permission:
            return await field_template_service.update_field_template(client_id, template_id, template)
        else:
            log_error(request.app.db, request, "Permission denied for update_field_template", None, {"client_id": client_id, "template_id": template_id})
            raise HTTPException(status_code=403, detail="Permission denied")
    except HTTPException as he:
        # Pass through HTTP exceptions with their status codes
        raise he
    except Exception as e:
        log_error(request.app.db, request, "Error updating field template", e, '')
        raise HTTPException(status_code=500, detail=f"Error updating field template: {str(e)}")

@field_template_router.patch("/field_templates/{template_id}")
async def delete_field_template(
    request: Request,
    template_id: str,
    client_id: str = Query(..., description="Client ID"),
    field_template_service: FieldTemplateService = Depends(get_field_template_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Field", "update")) or Depends(permission_required("Crop", "update"))
):
    try:
        if permission:
            return await field_template_service.delete_field_template(client_id, template_id)
        else:
            log_error(request.app.db, request, "Permission denied for delete_field_template", None, {"client_id": client_id, "template_id": template_id})
            raise HTTPException(status_code=403, detail="Permission denied")
    except HTTPException as he:
        raise he
    except Exception as e:
        log_error(request.app.db, request, "Error deleting field template", e, '')
        raise HTTPException(status_code=500, detail=f"Error deleting field template: {str(e)}")