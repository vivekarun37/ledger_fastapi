from datetime import datetime, timedelta
import traceback
import inspect
import logging
import jwt
from bson.objectid import ObjectId
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Optional, Any
from config import Config

def create_access_token(user_data: dict, expiry: timedelta = None, refresh: bool = False) -> str:
    clean_user_data = {}
    for key, value in user_data.items():
        if isinstance(value, ObjectId):
            clean_user_data[key] = str(value)
        elif isinstance(value, bytes):
            try:
                clean_user_data[key] = value.decode('utf-8')
            except UnicodeDecodeError:
                clean_user_data[key] = str(value)
        else:
            clean_user_data[key] = value
    
    payload = {
        'user': clean_user_data,
        'exp': datetime.now() + (expiry if expiry is not None else timedelta(minutes=60)),
        'jti': str(clean_user_data.get('id', ObjectId())),
        'refresh': refresh
    }
    
    token = jwt.encode(
        payload=payload,
        key=Config.JWT_SECRET,
        algorithm=Config.JWT_ALGORITHM
    )
    
    # Handle PyJWT's inconsistent return type across versions
    if isinstance(token, bytes):
        return token.decode('utf-8')
    return token

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        token_data = jwt.decode(
            jwt=token,
            key=Config.JWT_SECRET,
            algorithms=[Config.JWT_ALGORITHM]
        )
        return token_data
    except jwt.PyJWTError as jwte:
        logging.exception(jwte)
        return None
    except Exception as e:
        logging.exception(e)
        return None

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid authentication scheme."
                )
            if not self.verify_token(credentials.credentials):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid token or expired token."
                )
            token_data = decode_token(credentials.credentials)
            return token_data
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization code."
            )

    def verify_token(self, token: str) -> bool:
        is_token_valid: bool = False
        try:
            payload = decode_token(token)
            if payload:
                is_token_valid = True
        except:
            is_token_valid = False
        return is_token_valid

def get_current_user(token_data: dict = Depends(JWTBearer())) -> dict:
    if not token_data or "user" not in token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_data["user"]

def log_error(db, request: Request, error_message, exception=None, payload=None):
    try:
        frame = inspect.currentframe().f_back
        module_name = frame.f_globals['__name__']
        function_name = frame.f_code.co_name
        http_method = request.method
        timestamp = datetime.utcnow()
        
        # Handle JSON serialization issues
        safe_payload = payload
        if isinstance(payload, bytes):
            try:
                safe_payload = payload.decode('utf-8')
            except UnicodeDecodeError:
                safe_payload = str(payload)  # Fallback to string representation
        elif isinstance(payload, dict):
            # Process dictionaries to ensure all values are serializable
            safe_payload = {}
            for key, value in payload.items():
                if isinstance(value, bytes):
                    try:
                        safe_payload[key] = value.decode('utf-8')
                    except UnicodeDecodeError:
                        safe_payload[key] = str(value)
                elif isinstance(value, ObjectId):
                    safe_payload[key] = str(value)
                else:
                    safe_payload[key] = value
                    
        error_data = {
            "module": module_name,
            "method": http_method,
            "timestamp": timestamp,
            "payload": safe_payload,
            "description": str(exception) if exception else error_message
        }

        if db and hasattr(db, 'error_log'):
            db.error_log.insert_one(error_data)
        else:
            print(f"ERROR LOG (couldn't write to db): {error_data}")
    except Exception as ep:
        print(f"Failed to log error: {str(ep)}")

def check_permission(module: str, action: str, token_details: dict) -> bool:
    if not token_details or "user" not in token_details:
        print(f"Permission denied: No user in token")
        return False
    
    user_data = token_details["user"]
    
    # Check if permissions field exists
    if "permissions" not in user_data:
        print(f"Permission denied: No permissions in user data")
        return False
    
    permissions = user_data["permissions"]
    
    if module not in permissions:
        print(f"Permission denied: Module '{module}' not found in permissions")
        return False
    
    # Check if the action exists in the module permissions
    module_permissions = permissions[module]
    if action not in module_permissions:
        print(f"Permission denied: Action '{action}' not found in module '{module}'")
        return False
    
    has_permission = module_permissions[action]
    return has_permission

def permission_required(module: str, action: str):
    async def dependency(token_details: dict = Depends(JWTBearer())):
        has_permission = check_permission(module, action, token_details)
        return has_permission
    return dependency

def check_additional_permissions(module: str, feature: str, action: str, token_details: dict) -> bool:
    if not token_details or "user" not in token_details:
        print(f"Permission denied: No user in token")
        return False
    
    user_data = token_details["user"]
    
    # Check if permissions field exists
    if "permissions" not in user_data:
        print(f"Permission denied: No permissions in user data")
        return False
    
    permissions = user_data["permissions"]
    
    if module not in permissions:
        return False
    
    # Check if the feature exists in the module permissions
    module_permissions = permissions[module]
    if feature not in module_permissions:
        return False
    
    # Check if the action exists in the feature permissions
    feature_permissions = module_permissions[feature]
    if action not in feature_permissions:
        return False
    
    has_permission = feature_permissions[action]
    return has_permission

def additional_permissions_required(module: str, feature: str, action: str):
    async def dependency(token_details: dict = Depends(JWTBearer())):
        has_permission = check_additional_permissions(module, feature, action, token_details)
        return has_permission
    return dependency
