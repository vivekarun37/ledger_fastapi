from wsgiref.util import application_uri
from fastapi import APIRouter, Depends, Request, Body, Query, HTTPException, status
from models.farmModel import SensorData
from models.farmModel import Field
from models.farmModel import Form
from bson import ObjectId
from pymongo import MongoClient
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError
from datetime import datetime, timedelta
import pandas as pd
from bson import Int64
from pydantic import BaseModel
from typing import Dict ,List, Optional
from utils import log_error,permission_required,get_current_user




sensor_router = APIRouter(prefix="", tags=['Sensor'])


@sensor_router.get("/getdata")
async def getData(request: Request, date: str = Query(None), device_id: str = Query(None),
user: dict = Depends(get_current_user),
permission: bool = Depends(permission_required("Device", "read"))) -> List[SensorData]:
    if permission:
        db = request.app.farm 
        if not date or not device_id:
            return JSONResponse(
                content={"error": "Both 'date' and 'device_id' must be provided"},
                status_code=400
            )

        # Query the database to match both date and device_id
        response = list(db.find({"time": {"$regex": f"^{date}"}, "id": device_id}))
        
        # Modify the response to return stringified ObjectIds
        for item in response:
            item["_id"] = str(item["_id"])    
        
        return JSONResponse(content={"data": response})
    else:
        log_error(request.app, request, "Permission denied for getdata_route", None, {"device_id": device_id, "date": date})
        return JSONResponse(
            content={"error": "Permission denied"},
            status_code=status.HTTP_403_FORBIDDEN
        )


@sensor_router.get("/getdatafordisplay")
async def get_data(request: Request, date: str = Query(None),
user: dict = Depends(get_current_user),
permission: bool = Depends(permission_required("Device", "read"))) -> dict:
    if permission:
        db = request.app.farm

        # Default to today's date if none is provided
        if not date:
            date = datetime.now().strftime("%Y/%m/%d")
        
        # Extract the month and year from the given date
        try:
            parsed_date = datetime.strptime(date, "%Y/%m/%d")
            end_date = parsed_date
            start_date = end_date - timedelta(days=30)
            # current_month = parsed_date.strftime("%Y/%m")
        except ValueError:
            return JSONResponse(content={"error": "Invalid date format. Use YYYY/MM/DD."}, status_code=400)
        
        # Query MongoDB for all data for the extracted month
        response = list(db.find({
        "time": {
            "$gte": start_date.strftime("%Y/%m/%d"),
            "$lt": (end_date + timedelta(days=1)).strftime("%Y/%m/%d")
        }
    }))

        # Convert `_id` to string for JSON compatibility
        for item in response:
            item["_id"] = str(item["_id"])

        # Filter records for the specific day
        current_date_data = [item for item in response if item["time"].startswith(date)]

        # Initialize results
        latest_data_entries = {}
        min_max_values = {}
        monthly_daily_averages = {}

        if response:
            df = pd.DataFrame(response)
            df['time'] = pd.to_datetime(df['time'], errors='coerce')
            
            # Calculate daily averages for the entire month
            df['date'] = df['time'].dt.strftime("%Y/%m/%d")
            daily_averages_df = df.groupby('date').agg({
        'temperature': ['mean', 'max', 'min'],
        'humidity': ['mean', 'max', 'min'],
        'EC': ['mean', 'max', 'min']
    }).reset_index()
            daily_averages_df.columns = ['date', 
        'temperature_average', 'temperature_max', 'temperature_min',
        'humidity_average', 'humidity_max', 'humidity_min',
        'EC_average', 'EC_max', 'EC_min']
            # Convert to dictionary where each date is a key
        monthly_daily_averages = {
        row['date']: {
            "temperature": {
                "average": round(row['temperature_average'], 2),
                "max": round(row['temperature_max'], 2),
                "min": round(row['temperature_min'], 2),
            },
            "humidity": {
                "average": round(row['humidity_average'], 2),
                "max": round(row['humidity_max'], 2),
                "min": round(row['humidity_min'], 2),
            },
            "EC": {
                "average": round(row['EC_average'], 2),
                "max": round(row['EC_max'], 2),
                "min": round(row['EC_min'], 2),
            },
        }
        for _, row in daily_averages_df.iterrows()
    }

            # Process data for the current date
        if current_date_data:
                current_date_df = pd.DataFrame(current_date_data)

                # Latest entries for the specified day
                latest_entry = current_date_df.sort_values(by="time", ascending=False).iloc[0]
                latest_data_entries = {
                    "temperature": latest_entry["temperature"],
                    "humidity": latest_entry["humidity"],
                    "EC": latest_entry["EC"],
                }

                # Minimum and maximum values for the day
                min_max_values = {
                    "temperature": {
                        "min": round(current_date_df["temperature"].min(), 2),
                        "max": round(current_date_df["temperature"].max(), 2),
                    },
                    "humidity": {
                        "min": round(current_date_df["humidity"].min(), 2),
                        "max": round(current_date_df["humidity"].max(), 2),
                    },
                    "EC": {
                        "min": round(current_date_df["EC"].min(), 2),
                        "max": round(current_date_df["EC"].max(), 2),
                    },
                }
        else:
            # Handle cases where there is no data
            latest_data_entries = {}
            min_max_values = {}
            monthly_daily_averages = {}

        # Return the required data as dictionaries
        return JSONResponse(
            content={
                "current_date_data": current_date_data,
                "latest_data_entries": latest_data_entries,
                "min_max_values": min_max_values,
                "monthly_daily_averages": monthly_daily_averages,
            }
        )
    else:
        log_error(request.app, request, "Permission denied for get_data_route", None, {"date": date})
        return JSONResponse(
            content={"error": "Permission denied"},
            status_code=status.HTTP_403_FORBIDDEN
        )


@sensor_router.get("/getdatarange")
async def getDataRange(
    request: Request,
    start_date: str = Query(None),
    end_date: str = Query(None),
    device_id: str = Query(None),
    user: dict = Depends(get_current_user),
    permission: bool = Depends(permission_required("Device", "read"))
) -> list:
    db = request.app.farm

    try:
        if permission:
            start_datetime = datetime.strptime(start_date, "%Y/%m/%d")
            end_datetime = datetime.strptime(end_date, "%Y/%m/%d")+ timedelta(days=1) - timedelta(seconds=1)

            response = list(db.find({
                "time": {"$gte": start_datetime.strftime("%Y/%m/%d"),
                "$lte": end_datetime.strftime("%Y/%m/%d %H:%M:%S")},
                "id": device_id
            }))

            for item in response:
                item["_id"] = str(item["_id"])

            return JSONResponse(content={"data": response})
    
        else:
            log_error(request.app, request, "Permission denied for getdatarange_route", None, {"device_id": device_id, "start_date": start_date, "end_date": end_date})
            return JSONResponse(
                content={"error": "Permission denied"},
                status_code=status.HTTP_403_FORBIDDEN
            )

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)


@sensor_router.post("/device/save_log")
async def addData(request: Request):
    try:
        data = await request.json()
        db_farm = request.app.farm
        db_logs = request.app.logs        
        db_logs.insert_one({"type":"data","message":str(data)})
        response = db_farm.insert_one(data)
    except Exception as e:
        print(str(e))
        db_logs = request.app.logs
        db_logs.insert_one({"type":"error","message":str(e)})

