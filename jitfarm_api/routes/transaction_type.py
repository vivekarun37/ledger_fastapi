from fastapi import APIRouter, Depends, Request, Body, HTTPException, status
from jitfarm_api.models.farmModel import TransactionType
from jitfarm_api.services.transaction_type import TransactionTypeService
from jitfarm_api.utils import log_error, permission_required, get_current_user, additional_permissions_required
from typing import Dict, List

transaction_type_router = APIRouter(prefix="", tags=['TransactionType'])

def get_transaction_type_service(request: Request) -> TransactionTypeService:
    return TransactionTypeService(request.app)

@transaction_type_router.post("/add_transaction_type")
async def add_transaction_type(
    request: Request,
    transaction_type: TransactionType = Body(...),
    transaction_type_service: TransactionTypeService = Depends(get_transaction_type_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Account", "create")),
    additional_permission: bool = Depends(additional_permissions_required("Account", "TRANSACTION_TYPE", "create"))
):
    try:
        if permission or additional_permission:
            result = await transaction_type_service.add_transaction_type(transaction_type)
            return result
        else:
            log_error(request.app, request, "Permission denied for add_transaction_type", None, transaction_type.dict())
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to add transaction types"
            )
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in add_transaction_type: {e.detail}", e, transaction_type.dict())
        raise e
    except Exception as e:
        log_error(request.app, request, "Unexpected error in add_transaction_type", e, transaction_type.dict())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@transaction_type_router.get("/get_transaction_types")
async def get_transaction_types(
    request: Request,
    client_id: str,
    transaction_type_service: TransactionTypeService = Depends(get_transaction_type_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Account", "read")),
    additional_permission: bool = Depends(additional_permissions_required("Account", "TRANSACTION_TYPE", "read"))
):
    try:
        if permission or additional_permission:
            if not client_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Client ID is required"
                )
            transaction_types = await transaction_type_service.get_transaction_types(client_id)
            return transaction_types
        else:
            log_error(request.app, request, "Permission denied for get_transaction_types", None, {"client_id": client_id})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view transaction types"
            )
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in get_transaction_types: {e.detail}", e, {"client_id": client_id})
        raise e
    except Exception as e:
        log_error(request.app, request, "Unexpected error in get_transaction_types", e, {"client_id": client_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@transaction_type_router.put("/update_transaction_type/{transaction_type_id}")
async def update_transaction_type(
    request: Request,
    transaction_type_id: str,
    transaction_type: dict = Body(...),
    transaction_type_service: TransactionTypeService = Depends(get_transaction_type_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Account", "update")),
    additional_permission: bool = Depends(additional_permissions_required("Account", "TRANSACTION_TYPE", "update"))
):
    try:
        if permission or additional_permission:
            result = await transaction_type_service.update_transaction_type(transaction_type_id, transaction_type)
            return result
        else:
            log_error(request.app, request, "Permission denied for update_transaction_type", None, {"transaction_type_id": transaction_type_id, "transaction_type_data": transaction_type})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update transaction types"
            )
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in update_transaction_type: {e.detail}", e, {"transaction_type_id": transaction_type_id, "transaction_type_data": transaction_type})
        raise e
    except Exception as e:
        log_error(request.app, request, f"Unexpected error in update_transaction_type for transaction_type_id: {transaction_type_id}", e, {"transaction_type_id": transaction_type_id, "transaction_type_data": transaction_type})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@transaction_type_router.delete("/delete_transaction_type/{transaction_type_id}")
async def delete_transaction_type(
    request: Request,
    transaction_type_id: str,
    transaction_type_service: TransactionTypeService = Depends(get_transaction_type_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Account", "delete")),
    additional_permission: bool = Depends(additional_permissions_required("Account", "TRANSACTION_TYPE", "delete"))
):
    try:
        if permission or additional_permission:
            result = await transaction_type_service.delete_transaction_type(transaction_type_id)
            return result
        else:
            log_error(request.app, request, "Permission denied for delete_transaction_type", None, {"transaction_type_id": transaction_type_id})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete transaction types"
            )
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in delete_transaction_type: {e.detail}", e, {"transaction_type_id": transaction_type_id})
        raise e
    except Exception as e:
        log_error(request.app, request, f"Unexpected error in delete_transaction_type for transaction_type_id: {transaction_type_id}", e, {"transaction_type_id": transaction_type_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        ) 