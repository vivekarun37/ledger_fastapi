import os
from datetime import timedelta

class Config:
    JWT_SECRET = os.environ.get("JWT_SECRET", "your-secret-key-here")
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE = timedelta(minutes=300)
    JWT_REFRESH_TOKEN_EXPIRE = timedelta(days=7)
    
    # MongoDB Configuration
    MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb+srv://vivekarun6353:G7ZHTGZ77OzfeBXC@testnext.d8nktnu.mongodb.net/?tlsAllowInvalidCertificates=true")
    MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "npk")
   