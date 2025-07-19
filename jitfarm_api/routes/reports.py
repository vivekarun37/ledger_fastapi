from fastapi import APIRouter, Depends, Request, Query, HTTPException
from datetime import datetime
from typing import Optional
from services.profit_loss import ProfitLossService
from services.balance_sheet import BalanceSheetService
from utils import get_current_user, permission_required, log_error

reports_router = APIRouter(prefix="", tags=['Reports'])

def get_profit_loss_service(request: Request) -> ProfitLossService:
    return ProfitLossService(request.app)

def get_balance_sheet_service(request: Request) -> BalanceSheetService:
    return BalanceSheetService(request.app)

@reports_router.get("/profit_loss")
async def get_profit_loss(
    request: Request,
    client_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    group_by: str = Query("month", regex="^(month|quarter|year)$"),
    profit_loss_service: ProfitLossService = Depends(get_profit_loss_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Reports", "read"))
):
    try:
        if not permission:
            error_msg = "You don't have permission to view reports"
            log_error(request.app, request, error_msg, None, {"client_id": client_id})
            raise HTTPException(status_code=403, detail=error_msg)

        # Parse dates if provided
        start = None
        end = None
        if start_date:
            try:
                start = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")
        
        if end_date:
            try:
                end = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")

        result, exception = await profit_loss_service.get_profit_loss(
            client_id=client_id,
            start_date=start,
            end_date=end,
            group_by=group_by
        )

        if exception:
            error_msg = result.get("message", str(exception))
            log_error(request.app, request, f"Error generating P&L report: {error_msg}", exception)
            raise HTTPException(status_code=500, detail=error_msg)

        return result

    except HTTPException as e:
        raise e
    except Exception as e:
        error_msg = f"Unexpected error generating P&L report: {str(e)}"
        log_error(request.app, request, error_msg, e)
        raise HTTPException(status_code=500, detail=error_msg)

@reports_router.get("/balance_sheet")
async def get_balance_sheet(
    request: Request,
    client_id: str,
    based_on: str = Query("until_date", regex="^(until_date|fiscal_year)$"),
    to_date: Optional[str] = None,
    count: int = 1,
    from_year: Optional[int] = None,
    to_year: Optional[int] = None,
    periodicity: str = Query("monthly", regex="^(monthly|quarterly|half-yearly|yearly)$"),
    consolidate: bool = False,
    hide_group_amounts: bool = False,
    balance_sheet_service: BalanceSheetService = Depends(get_balance_sheet_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Reports", "read"))
):
    try:
        if not permission:
            error_msg = "You don't have permission to view reports"
            log_error(request.app, request, error_msg, None, {"client_id": client_id})
            raise HTTPException(status_code=403, detail=error_msg)

        # Parse to_date if provided
        to_date_parsed = None
        if to_date:
            try:
                to_date_parsed = datetime.fromisoformat(to_date)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid to_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")

        result = await balance_sheet_service.get_balance_sheet(
            client_id=client_id,
            based_on=based_on,
            to_date=to_date_parsed,
            count=count,
            from_year=from_year,
            to_year=to_year,
            periodicity=periodicity,
            consolidate=consolidate,
            hide_group_amounts=hide_group_amounts
        )
        return result

    except HTTPException as e:
        raise e
    except Exception as e:
        error_msg = f"Unexpected error generating Balance Sheet report: {str(e)}"
        log_error(request.app, request, error_msg, e)
        raise HTTPException(status_code=500, detail=error_msg) 