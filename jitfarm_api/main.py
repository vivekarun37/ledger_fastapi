from fastapi import FastAPI
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from jitfarm_api.routes.client import client_router
from jitfarm_api.routes.contact import contact_router
from jitfarm_api.routes.crop import crop_router
from jitfarm_api.routes.field import field_router
from jitfarm_api.routes.sensor import sensor_router
from jitfarm_api.routes.user import user_router
from jitfarm_api.routes.form import form_router
from jitfarm_api.routes.device import device_router
from jitfarm_api.routes.custom_field import field_template_router
from jitfarm_api.routes.role import role_router
from jitfarm_api.routes.coa import coa_router
from jitfarm_api.routes.transaction import transaction_router
from jitfarm_api.routes.ledger import ledger_router
from jitfarm_api.routes.reports import reports_router
from jitfarm_api.config import Config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def connectToDatabase(collection_name):
    # Connect to MongoDB using the full connection string
    client = AsyncIOMotorClient(Config.MONGODB_URI, tlsAllowInvalidCertificates=True)
    # Get the database
    db = client[Config.MONGODB_DB_NAME]
    return db

@asynccontextmanager
async def lifespan(app: FastAPI):
    db = await connectToDatabase("farm")
    app.db = db
    app.farm = db.farm    
    app.logs = db.logs
    app.users = db.users
    app.formFields = db.formFields
    app.form_data = db.form_data
    app.clients = db.clients
    app.devices = db.devices
    app.crops = db.crops
    app.fields = db.fields
    app.contacts = db.contacts
    app.countries_db = db.countries_db
    app.error_log = db.error_log
    app.field_templates = db.field_templates
    app.roles = db.roles
    app.permissions = db.permissions
    app.accounts = db.accounts
    app.transactions = db.transactions
    app.ledger = db.ledger
    
    print("startup has begun!!")
    yield
    print("shutdown has begun!!")

app = FastAPI(
    title="JitFarm API",
    description="API for JitFarm",
    version="1.0.0",
    lifespan=lifespan
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer Authentication": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter the JWT token with Bearer prefix, e.g. 'Bearer eyJhbGciOiJIUzI1NiIs...'"
        }
    }
    openapi_schema["security"] = [{"Bearer Authentication": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(client_router)
app.include_router(contact_router)
app.include_router(crop_router)
app.include_router(field_router)
app.include_router(sensor_router)
app.include_router(device_router)
app.include_router(user_router, prefix="/user")
app.include_router(form_router)
app.include_router(field_template_router)
app.include_router(role_router)
app.include_router(coa_router)
app.include_router(transaction_router)
app.include_router(ledger_router)
app.include_router(reports_router)

@app.get("/")
async def root():
    return {"message": "Welcome to JIT Farm API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8006, reload=True)