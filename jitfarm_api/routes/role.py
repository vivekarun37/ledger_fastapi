from fastapi import APIRouter, Request, HTTPException, status, Body, Depends, Query
from services.role import RoleService
from utils import log_error,get_current_user,permission_required
from typing import Dict, Any, Optional

role_router = APIRouter(prefix="", tags=['Roles'])

def get_role_service(request: Request) -> RoleService:
    return RoleService(request.app)

@role_router.post("/roles")
async def add_role_route(
    request: Request, 
    role: Dict[str, Any] = Body(...),
    role_service: RoleService = Depends(get_role_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Roles", "create"))
):
    try:
        if permission:
            inserted_id = role_service.add_role(role)
            return {"status": "success", "message": "Role added successfully", "id": inserted_id}
        else:
            log_error(request.app, request, "Permission denied for add_role_route", None, role)
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to add roles")
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in add_role_route: {e.detail}", e, role)
        raise e
    except Exception as e:
        log_error(request.app, request, "Error in add_role_route", e, role)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred")

@role_router.get("/roles")
async def get_roles_route(
    request: Request,
    client_id: Optional[str] = Query(None, description="Filter roles by client_id"),
    role_service: RoleService = Depends(get_role_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Roles", "read"))
):
    try:
        if permission:
            return role_service.get_all_roles(client_id)
        else:
            log_error(request.app, request, "Permission denied for get_roles_route", None, {"client_id": client_id})
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to get roles")
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in get_roles_route: {e.detail}", e, {"client_id": client_id})
        raise e
    except Exception as e:
        log_error(request.app, request, "Error in get_roles_route", e, {"client_id": client_id})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred")

@role_router.get("/roles/permissions")
async def get_role_permissions_route(request: Request
, role_service: RoleService = Depends(get_role_service), user: dict = Depends(get_current_user)):
    try:
        result = role_service.get_all_permissions() 
        return result
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in get_role_permissions_route: {e.detail}", e)
        raise e
    except Exception as e:
        print(f"Detailed error: {str(e)}")
        log_error(request.app, request, f"Error in get_role_permissions_route: {str(e)}", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An unexpected error occurred: {str(e)}"
        )
@role_router.get("/roles/{role_id}")
async def get_role_by_id_route(
    request: Request, 
    role_id: str,
    role_service: RoleService = Depends(get_role_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Roles", "read"))
):
    try:
        if permission:
            return role_service.get_role_by_id(role_id)
        else:
            log_error(request.app, request, "Permission denied for get_role_by_id_route", None, {"role_id": role_id})
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to get roles")
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in get_role_by_id_route: {e.detail}", e, {"role_id": role_id})
        raise e
    except Exception as e:
        log_error(request.app, request, f"Error in get_role_by_id_route for role {role_id}", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred")

@role_router.put("/roles/{role_id}")
async def update_role_route(
    request: Request, 
    role_id: str, 
    role: Dict[str, Any] = Body(...),
    role_service: RoleService = Depends(get_role_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Roles", "update"))
):
    try:
        if permission:
            return role_service.update_role(role_id, role)
        else:
            log_error(request.app, request, "Permission denied for update_role_route", None, {"role_id": role_id, "role_data": role})
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to update roles")
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in update_role_route: {e.detail}", e, {"role_id": role_id, "role_data": role})
        raise e
    except Exception as e:
        log_error(request.app, request, f"Error in update_role_route for role {role_id}", e, role)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred")

@role_router.delete("/roles/{role_id}")
async def delete_role_route(
    request: Request, 
    role_id: str,
    role_service: RoleService = Depends(get_role_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Roles", "delete"))
):
    try:
        if permission:
            return role_service.delete_role(role_id)
        else:
            log_error(request.app, request, "Permission denied for delete_role_route", None, {"role_id": role_id})
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have permission to delete roles")
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in delete_role_route: {e.detail}", e, {"role_id": role_id})
        raise e
    except Exception as e:
        log_error(request.app, request, f"Error in delete_role_route for role {role_id}", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred")