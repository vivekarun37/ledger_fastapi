from fastapi import APIRouter, Depends, Request, Body, HTTPException, status
from jitfarm_api.models.farmModel import Contacts
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from jitfarm_api.utils import log_error, get_current_user, permission_required
from jitfarm_api.services.contact import ContactService
from typing import List, Dict, Any

contact_router = APIRouter(prefix="", tags=['Contact'])

def get_contact_service(request: Request) -> ContactService:
    return ContactService(request.app)

@contact_router.post("/add_contact")
async def add_contact(
    request: Request,
    contact: Contacts,
    contact_service: ContactService = Depends(get_contact_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Contacts", "create"))

):
    try:
        if permission:
            result = await contact_service.add_contact(contact)
            return result
        else:
            log_error(request.app, request, "Permission denied for add_contact", None, contact.dict())
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to add contacts"
            )
    except RequestValidationError as e:
        log_error(request.app, request, "Validation error in add_contact", e, contact.dict())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"message": "Validation failed", "errors": e.errors()},
        )
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in add_contact: {e.detail}", e, contact.dict())
        raise e
    except Exception as e:
        log_error(request.app, request, "Unexpected error in add_contact", e, contact.dict())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@contact_router.get("/get_contacts")
async def get_contacts(
    request: Request,
    client_id: str,
    contact_service: ContactService = Depends(get_contact_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Contacts", "read"))
):
    try:
        if permission:
            contacts = await contact_service.get_contacts(client_id)
            return contacts
        else:
            log_error(request.app, request, "Permission denied for get_contacts", None, {"client_id": client_id})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view contacts"
            )
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in get_contacts: {e.detail}", e, {"client_id": client_id})
        raise e
    except Exception as e:
        log_error(request.app, request, f"Error in get_contacts for client_id: {client_id}", e, {"client_id": client_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@contact_router.put("/update_contact/{contact_id}")
async def update_contact(
    request: Request,
    contact_id: str,
    contact: Contacts = Body(...),
    contact_service: ContactService = Depends(get_contact_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Contacts", "update"))
):
    try:
        if permission:
            result = await contact_service.update_contact(contact_id, contact)
            return result
        else:
            log_error(request.app, request, "Permission denied for update_contact", None, 
                     {"contact_id": contact_id, "contact": contact.dict()})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update contacts"
            )
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in update_contact: {e.detail}", e, 
                 {"contact_id": contact_id, "contact": contact.dict()})
        raise e
    except Exception as e:
        log_error(request.app, request, f"Error in update_contact for contact_id: {contact_id}", e, 
                 {"contact_id": contact_id, "contact": contact.dict()})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@contact_router.delete("/delete_contact/{contact_id}")
async def delete_contact(
    request: Request,
    contact_id: str,
    contact_service: ContactService = Depends(get_contact_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Contacts", "delete"))
):
    try:
        if permission:
            result = await contact_service.delete_contact(contact_id)
            return result
        else:
            log_error(request.app, request, "Permission denied for delete_contact", None, {"contact_id": contact_id})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete contacts"
            )
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in delete_contact: {e.detail}", e, {"contact_id": contact_id})
        raise e
    except Exception as e:
        log_error(request.app, request, f"Error in delete_contact for contact_id: {contact_id}", e, {"contact_id": contact_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@contact_router.get("/get_countries")
async def get_countries(
    request: Request,
    contact_service: ContactService = Depends(get_contact_service)
):
    try:
        countries = await contact_service.get_countries()
        return countries
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in get_countries: {e.detail}", e)
        raise e
    except Exception as e:
        log_error(request.app, request, "Error in get_countries", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )