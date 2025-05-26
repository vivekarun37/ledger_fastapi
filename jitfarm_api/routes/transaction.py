from fastapi import APIRouter, Depends, Request, Body, Query, HTTPException, status
from models.farmModel import Transaction  # You'll need to create this model class
from services.transaction import TransactionService
from utils import log_error, permission_required, get_current_user, additional_permissions_required
from typing import Dict, List, Optional

transaction_router = APIRouter(prefix="", tags=['Transactions'])

def get_transaction_service(request: Request) -> TransactionService:
    return TransactionService(request.app)

@transaction_router.post("/add_transaction")
async def add_transaction(
    request: Request,
    transaction: dict = Body(...),
    transaction_service: TransactionService = Depends(get_transaction_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Account", "create")),
    additional_permission: bool = Depends(additional_permissions_required("Account", "TRANSACTION", "create"))
):
    try:
        if permission or additional_permission:
            result = await transaction_service.add_transaction(transaction)
            return result
        else:
            log_error(request.app, request, "Permission denied for add_transaction", None, transaction)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to add transactions"
            )
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in add_transaction: {e.detail}", e, transaction)
        raise e
    except Exception as e:
        log_error(request.app, request, "Unexpected error in add_transaction", e, transaction)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@transaction_router.get("/get_transactions")
async def get_transactions(
    request: Request,
    client_id: str,
    transaction_service: TransactionService = Depends(get_transaction_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Account", "read")),
    additional_permission: bool = Depends(additional_permissions_required("Account", "TRANSACTION", "read"))
):
    try:
        if permission or additional_permission:
            if not client_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Client ID is required"
                )
            transactions = await transaction_service.get_transactions(client_id)
            return transactions
        else:
            log_error(request.app, request, "Permission denied for get_transactions", None, {"client_id": client_id})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view transactions"
            )
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in get_transactions: {e.detail}", e, {"client_id": client_id})
        raise e
    except Exception as e:
        log_error(request.app, request, "Unexpected error in get_transactions", e, {"client_id": client_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@transaction_router.get("/get_all")
async def get_all(
    request: Request,
    client_id: str,
    transaction_service: TransactionService = Depends(get_transaction_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Account", "read")),
    additional_permission: bool = Depends(additional_permissions_required("Account", "TRANSACTION", "read"))
):
    try:
        if permission or additional_permission:
            transactions = await transaction_service.get_all(client_id)
            return transactions
        else:
            log_error(request.app, request, "Permission denied for get_all", None)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view all transactions"
            )
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in get_all: {e.detail}", e)
        raise e
    except Exception as e:
        log_error(request.app, request, "Unexpected error in get_all", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@transaction_router.put("/update_transaction/{transaction_id}")
async def update_transaction(
    request: Request,
    transaction_id: str,
    transaction: dict = Body(...),
    transaction_service: TransactionService = Depends(get_transaction_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Account", "update")),
    additional_permission: bool = Depends(additional_permissions_required("Account", "TRANSACTION", "update"))
):
    try:
        if permission or additional_permission:
            result = await transaction_service.update_transaction(transaction_id, transaction)
            return result
        else:
            log_error(request.app, request, "Permission denied for update_transaction", None, {"transaction_id": transaction_id, "transaction_data": transaction})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update transactions"
            )
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in update_transaction: {e.detail}", e, {"transaction_id": transaction_id, "transaction_data": transaction})
        raise e
    except Exception as e:
        log_error(request.app, request, f"Unexpected error in update_transaction for transaction_id: {transaction_id}", e, {"transaction_id": transaction_id, "transaction_data": transaction})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@transaction_router.delete("/delete_transaction/{transaction_id}")
async def delete_transaction(
    request: Request,
    transaction_id: str,
    transaction_service: TransactionService = Depends(get_transaction_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Account", "delete")),
    additional_permission: bool = Depends(additional_permissions_required("Account", "TRANSACTION", "delete"))
):
    try:
        if permission or additional_permission:
            result = await transaction_service.delete_transaction(transaction_id)
            return result
        else:
            log_error(request.app, request, "Permission denied for delete_transaction", None, {"transaction_id": transaction_id})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete transactions"
            )
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in delete_transaction: {e.detail}", e, {"transaction_id": transaction_id})
        raise e
    except Exception as e:
        log_error(request.app, request, f"Unexpected error in delete_transaction for transaction_id: {transaction_id}", e, {"transaction_id": transaction_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )