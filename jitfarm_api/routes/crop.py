from fastapi import APIRouter, Depends, Request, Body, Query, HTTPException, status
from models.farmModel import Crops
from services.crop import CropService
from utils import log_error,permission_required,get_current_user
from typing import Dict, List, Optional

crop_router = APIRouter(prefix="", tags=['Crop'])

def get_crop_service(request: Request) -> CropService:
    return CropService(request.app)

@crop_router.post("/add_crop")
async def add_crop(
    request: Request,
    crop: Crops,
    crop_service: CropService = Depends(get_crop_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Crop", "create"))
):
    try:
        if permission:
            result = await crop_service.add_crop(crop)
            return result
        else:
            log_error(request.app, request, "Permission denied for add_crop", None, crop.dict())
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to add crops"
            )
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in add_crop: {e.detail}", e, crop.dict())
        raise e
    except Exception as e:
        log_error(request.app, request, "Unexpected error in add_crop", e, crop.dict())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@crop_router.get("/get_crops")
async def get_crops(
    request: Request,
    client_id: str,
    crop_service: CropService = Depends(get_crop_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Crop", "read"))
):
    try:
        if permission:
            crops = await crop_service.get_crops(client_id)
            return crops
        else:
            log_error(request.app, request, "Permission denied for get_crops", None, {"client_id": client_id})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to get crops"
            )
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in get_crops: {e.detail}", e, {"client_id": client_id})
        raise e
    except Exception as e:
        log_error(request.app, request, f"Unexpected error in get_crops for client_id: {client_id}", e, {"client_id": client_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@crop_router.put("/update_crop/{crop_id}")
async def update_crop(
    request: Request,
    crop_id: str,
    crop: dict = Body(...),
    crop_service: CropService = Depends(get_crop_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Crop", "update"))
):
    try:
        if permission:
            result = await crop_service.update_crop(crop_id, crop)
            return result
        else:
            log_error(request.app, request, "Permission denied for update_crop", None, {"crop_id": crop_id, "crop_data": crop})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update crops"
            )
    except HTTPException as e:
        # Log the HTTP exception from service
        log_error(request.app, request, f"HTTP error in update_crop: {e.detail}", e, {"crop_id": crop_id, "crop_data": crop})
        raise e
    except Exception as e:
        # Log any unexpected errors
        log_error(request.app, request, f"Unexpected error in update_crop for crop_id: {crop_id}", e, {"crop_id": crop_id, "crop_data": crop})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@crop_router.delete("/delete_crop")
async def delete_crop(
    request: Request,
    crop_id: str = Query(...),
    crop_service: CropService = Depends(get_crop_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Crop", "delete"))
):
    try:
        if permission:
            result = await crop_service.delete_crop(crop_id)
            return result
        else:
            log_error(request.app, request, "Permission denied for delete_crop", None, {"crop_id": crop_id})
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete crops"
            )
    except HTTPException as e:
        log_error(request.app, request, f"HTTP error in delete_crop: {e.detail}", e, {"crop_id": crop_id})
        raise e
    except Exception as e:
        log_error(request.app, request, f"Unexpected error in delete_crop for crop_id: {crop_id}", e, {"crop_id": crop_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )