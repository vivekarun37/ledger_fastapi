from fastapi import APIRouter, Depends, Request, Body, Query, HTTPException, status
from models.farmModel import COAccount  # This should likely be renamed to match new naming
from services.coa import COAccountService
from utils import log_error, permission_required, get_current_user, additional_permissions_required
from typing import Dict, List, Optional
from datetime import datetime

coa_router = APIRouter(prefix="", tags=['ChartOfAccounts'])

def get_account_service(request: Request) -> COAccountService:
    return COAccountService(request.app)

@coa_router.post("/add_account")
async def add_account(
    request: Request,
    account: COAccount,
    account_service: COAccountService = Depends(get_account_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Account", "create")),
    additional_permission: bool = Depends(additional_permissions_required("Account", "COA", "create"))
):
    try:
        if permission or additional_permission:
            result = await account_service.add_account(account)
            return result
        else:
            log_error(request.app, request, "Permission denied for add_account", None, account.dict())
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to add accounts"
            )
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in add_account: {e.detail}", e, account.dict())
        raise e
    except Exception as e:
        log_error(request.app, request, "Unexpected error in add_account", e, account.dict())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@coa_router.get("/get_accounts")
async def get_accounts(
    request: Request,
    client_id: str,
    account_service: COAccountService = Depends(get_account_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Account", "read")) ,
    additional_permission: bool = Depends(additional_permissions_required("Account","COA", "read"))
):
    try:
        if permission or additional_permission:
            if not client_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Client ID not found in user context"
                )
            accounts = await account_service.get_accounts(client_id)
            return accounts
        else:
            log_error(request.app, request, "Permission denied for get_accounts", None, {"user": user})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view accounts"
            )
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in get_accounts: {e.detail}", e, {"user": user})
        raise e
    except Exception as e:
        log_error(request.app, request, "Unexpected error in get_accounts", e, {"user": user})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@coa_router.get("/get_active_accounts")
async def get_active_accounts(
    request: Request,
    client_id: str,
    account_service: COAccountService = Depends(get_account_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Account", "read")),
    additional_permission: bool = Depends(additional_permissions_required("Account","COA", "read"))
):
    try:
        if permission or additional_permission:
            if not client_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Client ID not found in user context"
                )
            accounts = await account_service.active_accounts(client_id)
            return accounts
        else:
            log_error(request.app, request, "Permission denied for get_active_accounts", None, {"user": user})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view active accounts"
            )
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in get_active_accounts: {e.detail}", e, {"user": user})
        raise e
    except Exception as e:
        log_error(request.app, request, "Unexpected error in get_active_accounts", e, {"user": user})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@coa_router.put("/update_account/{account_id}")
async def update_account(
    request: Request,
    account_id: str,
    account: dict = Body(...),
    account_service: COAccountService = Depends(get_account_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Account", "update")),
    additional_permission: bool = Depends(additional_permissions_required("Account", "COA", "update"))
):
    try:
        if permission or additional_permission:
            result = await account_service.update_account(account_id, account)
            return result
        else:
            log_error(request.app, request, "Permission denied for update_account", None, {"account_id": account_id, "account_data": account})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update accounts"
            )
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in update_account: {e.detail}", e, {"account_id": account_id, "account_data": account})
        raise e
    except Exception as e:
        log_error(request.app, request, f"Unexpected error in update_account for account_id: {account_id}", e, {"account_id": account_id, "account_data": account})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@coa_router.delete("/delete_account/{account_id}")
async def delete_account(
    request: Request,
    account_id: str,
    account_service: COAccountService = Depends(get_account_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Account", "delete")),
    additional_permission: bool = Depends(additional_permissions_required("Account", "COA", "delete"))
):
    try:
        if permission or additional_permission:
            result = await account_service.delete_account(account_id)
            return result
        else:
            log_error(request.app, request, "Permission denied for delete_account", None, {"account_id": account_id})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete accounts"
            )
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in delete_account: {e.detail}", e, {"account_id": account_id})
        raise e
    except Exception as e:
        log_error(request.app, request, f"Unexpected error in delete_account for account_id: {account_id}", e, {"account_id": account_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@coa_router.get("/account_ledger/{account_id}")
async def get_account_ledger(
    request: Request,
    account_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    account_service: COAccountService = Depends(get_account_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Account", "read")),
    additional_permission: bool = Depends(additional_permissions_required("Account", "COA", "read"))
):
    try:
        if permission or additional_permission:
            # Convert dates if provided
            start_date_obj = datetime.fromisoformat(start_date) if start_date else None
            end_date_obj = datetime.fromisoformat(end_date) if end_date else None
            
            result = await account_service.get_account_ledger(account_id, start_date_obj, end_date_obj)
            return result
        else:
            log_error(request.app, request, "Permission denied for get_account_ledger", None, {"account_id": account_id})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view account ledger"
            )
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in get_account_ledger: {e.detail}", e, {"account_id": account_id})
        raise e
    except Exception as e:
        log_error(request.app, request, "Unexpected error in get_account_ledger", e, {"account_id": account_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )