from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jitfarm_api.models.farmModel import Users, UserLogin
from jitfarm_api.services.user import UserService
from jitfarm_api.utils import get_current_user, get_db, create_access_token
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
user_router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@user_router.post("/login")
async def login(username: str = Form(), password: str = Form(), db=Depends(get_db)):
    try:
        user_service = UserService(db.users, db.clients, db.logs)
        result = await user_service.authenticate_user(username, password)
        
        if not result or result.get("status") != "success":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Generate access token
        access_token = create_access_token(
            user_data=result,
            expiry=timedelta(minutes=60)
        )
        
        return {
            "status": "success",
            "access_token": access_token,
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@user_router.post("/users")
async def add_user(user_data: Users, current_user=Depends(get_current_user), db=Depends(get_db)):
    try:
        # Set creation metadata
        user_data.created_by = current_user["user_name"]
        user_data.created_dt = datetime.utcnow()
        user_data.updated_by = current_user["user_name"]
        user_data.updated_dt = datetime.utcnow()
        
        user_service = UserService(db.users, db.clients, db.logs)
        result = await user_service.add_user(user_data)
        
        if result["status"] == "fail":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return result
    except Exception as e:
        logger.error(f"Add user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@user_router.get("/users/{client_id}")
async def get_users(client_id: str, current_user=Depends(get_current_user), db=Depends(get_db)):
    try:
        user_service = UserService(db.users, db.clients, db.logs)
        result = await user_service.get_users_by_client(client_id)
        
        if result["status"] == "fail":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["message"]
            )
        
        return result
    except Exception as e:
        logger.error(f"Get users error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@user_router.put("/users/{user_id}")
async def update_user(user_id: str, user_data: dict, current_user=Depends(get_current_user), db=Depends(get_db)):
    try:
        # Set update metadata
        user_data["updated_by"] = current_user["user_name"]
        user_data["updated_dt"] = datetime.utcnow()
        
        user_service = UserService(db.users, db.clients, db.logs)
        result = await user_service.update_user(user_id, user_data)
        
        if result["status"] == "fail":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return result
    except Exception as e:
        logger.error(f"Update user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@user_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user=Depends(get_current_user), db=Depends(get_db)):
    try:
        user_service = UserService(db.users, db.clients, db.logs)
        result = await user_service.delete_user(user_id)
        
        if result["status"] == "fail":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["message"]
            )
        
        return result
    except Exception as e:
        logger.error(f"Delete user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 