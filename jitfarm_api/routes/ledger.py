from fastapi import APIRouter, Depends, Request, HTTPException, Query
from jitfarm_api.models.ledgerModel import LedgerEntry, LedgerUpdate
from jitfarm_api.utils import log_error, get_current_user, permission_required, additional_permissions_required
from jitfarm_api.services.ledger import LedgerService
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

ledger_router = APIRouter(prefix="/ledger", tags=["Ledger"])

def get_ledger_service(request: Request) -> LedgerService:
    return LedgerService(
        ledger_collection=request.app.ledger,
        coa_collection=request.app.accounts
    )

@ledger_router.post("/entry", response_model=Dict)
async def create_ledger_entry(
    request: Request,
    entry: LedgerEntry,
    ledger_service: LedgerService = Depends(get_ledger_service),
    current_user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Ledger", "create"))
):
    """Create a new ledger entry"""
    try:
        if not permission:
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Set the created_by field from the current user
        entry.created_by = current_user.get("user_name", "admin")
        
        logger.info(f"Creating ledger entry: {entry.dict()}")
        result = await ledger_service.create_ledger_entry(entry)
        logger.info(f"Ledger entry created: {result}")
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in create_ledger_entry: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating ledger entry: {str(e)}")

@ledger_router.get("/entries/{coa_id}", response_model=List[Dict])
async def get_ledger_entries(
    request: Request,
    coa_id: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=1000),
    ledger_service: LedgerService = Depends(get_ledger_service),
    current_user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Ledger", "read"))
):
    """Get all ledger entries for a specific Chart of Account"""
    if not permission:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    return await ledger_service.get_ledger_entries(coa_id, skip, limit)

@ledger_router.get("/entry/{entry_id}", response_model=Dict)
async def get_ledger_entry(
    request: Request,
    entry_id: str,
    ledger_service: LedgerService = Depends(get_ledger_service),
    current_user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Ledger", "read"))
):
    """Get a specific ledger entry by ID"""
    if not permission:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    return await ledger_service.get_ledger_entry(entry_id)

@ledger_router.put("/entry/{entry_id}", response_model=Dict)
async def update_ledger_entry(
    request: Request,
    entry_id: str,
    update_data: LedgerUpdate,
    ledger_service: LedgerService = Depends(get_ledger_service),
    current_user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Ledger", "update"))
):
    """Update a ledger entry"""
    if not permission:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    update_data.updated_by = current_user.get("user_name", "admin")
    return await ledger_service.update_ledger_entry(entry_id, update_data)

@ledger_router.delete("/entry/{entry_id}", response_model=Dict)
async def delete_ledger_entry(
    request: Request,
    entry_id: str,
    ledger_service: LedgerService = Depends(get_ledger_service),
    current_user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Ledger", "delete"))
):
    """Delete a ledger entry (soft delete)"""
    if not permission:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    return await ledger_service.delete_ledger_entry(entry_id, current_user.get("user_name", "admin"))

@ledger_router.get("/balance/{coa_id}", response_model=Dict)
async def get_ledger_balance(
    request: Request,
    coa_id: str,
    ledger_service: LedgerService = Depends(get_ledger_service),
    current_user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Ledger", "read"))
):
    """Get the current balance for a specific Chart of Account"""
    if not permission:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    return await ledger_service.get_ledger_balance(coa_id) 