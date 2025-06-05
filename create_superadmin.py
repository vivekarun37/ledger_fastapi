from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import hashlib
import asyncio
from jitfarm_api.config import Config
from bson import ObjectId

async def create_superadmin():
    # Connect to MongoDB
    client = AsyncIOMotorClient(Config.MONGODB_URI, tlsAllowInvalidCertificates=True)
    db = client[Config.MONGODB_DB_NAME]
    
    # Create superadmin client
    client_data = {
        "name": "Superadmin Organization",
        "description": "Superadmin organization with full system access",
        "client_code": "SUPERADMIN",
        "created_by": "system",
        "created_dt": datetime.utcnow(),
        "updated_by": "system",
        "updated_dt": datetime.utcnow()
    }
    
    print("Creating superadmin client...")
    result = await db.clients.insert_one(client_data)
    client_id = result.inserted_id
    
    # Create superadmin role
    role_data = {
        "client_id": client_id,  # Store as ObjectId
        "name": "superadmin",
        "description": "Superadmin role with full system access",
        "is_system_generated": True,
        "permissions": {
            "Account": {
                "read": True,
                "create": True,
                "update": True,
                "delete": True
            },
            "Contacts": {
                "read": True,
                "create": True,
                "update": True,
                "delete": True
            },
            "Device": {
                "read": True,
                "create": True,
                "update": True,
                "delete": True
            },
            "Crop": {
                "read": True,
                "create": True,
                "update": True,
                "delete": True
            },
            "Field": {
                "read": True,
                "create": True,
                "update": True,
                "delete": True
            },
            "Users": {
                "read": True,
                "create": True,
                "update": True,
                "delete": True
            },
            "Roles": {
                "read": True,
                "create": True,
                "update": True,
                "delete": True
            },
            "Data Addition": {
                "read": True,
                "create": True,
                "update": True,
                "delete": True
            },
            "Clients": {
                "read": True,
                "create": True,
                "update": True,
                "delete": True
            }
        },
        "created_by": "system",
        "created_dt": datetime.utcnow()
    }
    
    print("Creating superadmin role...")
    result = await db.roles.insert_one(role_data)
    role_id = result.inserted_id
    
    # Create superadmin user
    hashed_password = hashlib.md5("admin123".encode()).hexdigest()
    user_data = {
        "user_name": "admin",
        "password": hashed_password,
        "email": "admin@superadmin.com",
        "client_id": client_id,  # Store as ObjectId
        "role_permissions": role_data["permissions"],
        "role_name": "superadmin",
        "role": role_id,
        "is_system_generated": True,
        "created_by": "system",
        "created_dt": datetime.utcnow(),
        "updated_by": "system",
        "updated_dt": datetime.utcnow()
    }
    
    print("Creating superadmin user...")
    result = await db.users.insert_one(user_data)
    user_id = result.inserted_id
    
    print("\nSuperadmin setup complete!")
    print(f"Client ID: {client_id}")
    print(f"Role ID: {role_id}")
    print(f"User ID: {user_id}")
    print("\nLogin credentials:")
    print("Username: admin")
    print("Password: admin123")

if __name__ == "__main__":
    asyncio.run(create_superadmin()) 