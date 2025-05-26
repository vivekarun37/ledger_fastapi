from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
import logging
from jitfarm_api.routes.coa import coa_router
from datetime import datetime
from bson import ObjectId

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# MongoDB connection
@app.on_event("startup")
async def startup_db_client():
    try:
        logger.info("Connecting to MongoDB...")
        app.mongodb_client = MongoClient("mongodb://localhost:27017")
        # Test the connection
        app.mongodb_client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        app.accounts = app.mongodb_client.nextai.accounts
        app.transactions = app.mongodb_client.nextai.transactions
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection failed")

@app.on_event("shutdown")
async def shutdown_db_client():
    logger.info("Closing MongoDB connection...")
    app.mongodb_client.close()

# Include routers
app.include_router(coa_router)

# Test endpoint without authentication
@app.get("/test_ledger/{account_id}")
async def test_ledger(account_id: str):
    try:
        # Get account details
        account = app.accounts.find_one({"_id": ObjectId(account_id)})
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        # Get transactions
        transactions = list(app.transactions.find({"account_id": account_id}).sort("date", 1))

        # Calculate running balance
        running_balance = 0
        for transaction in transactions:
            transaction["_id"] = str(transaction["_id"])
            amount = float(transaction.get("amount", 0))
            
            if transaction.get("type") == "debit":
                if account.get("account_type") in ["Asset", "Expense"]:
                    running_balance += amount
                else:
                    running_balance -= amount
            else:  # credit
                if account.get("account_type") in ["Asset", "Expense"]:
                    running_balance -= amount
                else:
                    running_balance += amount
            
            transaction["running_balance"] = running_balance

        return {
            "status": "success",
            "account": {
                "id": str(account["_id"]),
                "code": account.get("account_code"),
                "name": account.get("account_name"),
                "type": account.get("account_type"),
                "subtype": account.get("account_subtype")
            },
            "transactions": transactions,
            "current_balance": running_balance
        }

    except Exception as e:
        logger.error(f"Error in test_ledger: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Test endpoint
@app.get("/")
async def root():
    return {"message": "API is running"} 