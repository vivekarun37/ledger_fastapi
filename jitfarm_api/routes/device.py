from fastapi import APIRouter, Depends, Request, Body, Query, HTTPException
from models.farmModel import Device
from services.device import DeviceService
from typing import Dict, List, Optional
from utils import log_error,get_current_user,permission_required

device_router = APIRouter(prefix="", tags=['Device'])

# Helper function to get the device service
def get_device_service(request: Request) -> DeviceService:
    return DeviceService(request.app)

@device_router.post("/add_device")
async def add_device(
    request: Request,
    device: Device,
    device_service: DeviceService = Depends(get_device_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Device", "create"))
):
    try:
        if permission:
            return await device_service.add_device(device)
        else:
            log_error(request.app, request, "Permission denied for add_device", None, device.dict())
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to add devices"
            )
    except Exception as e:
        log_error(request.app, request, "Failed to add device", e, payload=device.dict())
        raise

@device_router.get("/get_devices")
async def get_devices(
    request: Request,
    client_id: str,
    device_service: DeviceService = Depends(get_device_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Device", "read"))
):
    try:
        if permission:
            return await device_service.get_devices(client_id)
        else:
            log_error(request.app, request, "Permission denied for get_devices", None, {"client_id": client_id})
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to get devices"
            )
    except Exception as e:
        log_error(request.app, request, f"Failed to retrieve devices for client {client_id}", e)
        raise

@device_router.put("/update_device/{device_id}")
async def update_device(
    request: Request,
    device_id: str,
    device_data: dict = Body(...),
    device_service: DeviceService = Depends(get_device_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Device", "update"))
):
    try:
        if permission:
            return await device_service.update_device(device_id, device_data)
        else:
            log_error(request.app, request, "Permission denied for update_device", None, {"device_id": device_id, "device_data": device_data})
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to update devices"
            )
    except Exception as e:
        log_error(request.app, request, f"Failed to update device {device_id}", e, payload=device_data)
        raise

@device_router.post("/activate_devices")
async def activate_devices(
    request: Request,
    device_ids: List[str] = Body(..., embed=True),
    device_service: DeviceService = Depends(get_device_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Field", "update"))
):
    try:
        if permission:
            return await device_service.activate_devices(device_ids)
        else:
            log_error(request.app, request, "Permission denied for activate_devices", None, {"device_ids": device_ids})
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to activate devices"
            )
    except Exception as e:
        log_error(request.app, request, "Failed to activate devices", e, payload={"device_ids": device_ids})
        raise

@device_router.post("/deactivate_devices")
async def deactivate_devices(
    request: Request,
    device_ids: List[str] = Body(..., embed=True),
    device_service: DeviceService = Depends(get_device_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Field", "update"))
):
    try:
        if permission:
            return await device_service.deactivate_devices(device_ids)
        else:
            log_error(request.app, request, "Permission denied for deactivate_devices", None, {"device_ids": device_ids})
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to deactivate devices"
            )
    except Exception as e:
        log_error(request.app, request, "Failed to deactivate devices", e, payload={"device_ids": device_ids})
        raise

@device_router.delete("/delete_device/{device_id}")
async def delete_device(
    request: Request,
    device_id: str,
    device_service: DeviceService = Depends(get_device_service),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Device", "delete"))
):
    try:
        if permission:
            return await device_service.delete_device(device_id)
        else:
            log_error(request.app, request, "Permission denied for delete_device", None, {"device_id": device_id})
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to delete devices"
            )
    except Exception as e:
        log_error(request.app, request, f"Failed to delete device {device_id}", e)
        raise