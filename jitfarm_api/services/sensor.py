from datetime import datetime, timedelta
import pandas as pd
from bson import ObjectId
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError
import traceback
import inspect

class SensorService:
    def __init__(self, db_farm, db_logs, db_error_log=None):
        """
        Initialize Sensor Service with database connections
        
        Args:
            db_farm: MongoDB collection for farm data
            db_logs: MongoDB collection for general logs
            db_error_log: MongoDB collection for detailed error logs
        """
        self.db_farm = db_farm
        self.db_logs = db_logs
        self.db_error_log = db_error_log

    def log_error(self, error_message, exception=None):
        """
        Log error details to the database including module name and stack trace
        
        Args:
            error_message: Description of the error
            exception: Exception object (optional)
        """
        # Get caller frame information
        frame = inspect.currentframe().f_back
        module_name = frame.f_globals['__name__']
        function_name = frame.f_code.co_name
        line_number = frame.f_lineno
        
        # Build error data with more details
        error_data = {
            "error": error_message,
            "module": module_name,
            "function": function_name,
            "line": line_number,
            "timestamp": datetime.utcnow()
        }
        
        # Add exception details if provided
        if exception:
            error_data["exception_type"] = type(exception).__name__
            error_data["exception_message"] = str(exception)
            
            # Get and format traceback
            tb = traceback.format_exc()
            error_data["traceback"] = tb
        
        # Insert error into database
        if self.db_error_log:
            try:
                self.db_error_log.insert_one(error_data)
            except Exception as e:
                # Fallback if error logging fails
                print(f"ERROR LOG (couldn't write to error_log db): {error_data}")
                print(f"Meta-error: {str(e)}")
        
        # Always log to general logs as well
        try:
            self.db_logs.insert_one({"type": "error", "message": error_message, "details": error_data})
        except Exception as e:
            # Final fallback
            print(f"ERROR LOG (couldn't write to logs db): {error_data}")
            print(f"Meta-error: {str(e)}")

    async def get_data(self, date, device_id):
        """
        Get sensor data for a specific date and device ID
        
        Args:
            date: Date string in format YYYY/MM/DD
            device_id: Device identifier
            
        Returns:
            JSONResponse with data or error message
        """
        try:
            # Check if both date and device_id are provided
            if not date or not device_id:
                return JSONResponse(
                    content={"error": "Both 'date' and 'device_id' must be provided"},
                    status_code=400
                )

            # Query the database to match both date and device_id
            response = list(self.db_farm.find({"time": {"$regex": f"^{date}"}, "id": device_id}))
            
            # Modify the response to return stringified ObjectIds
            for item in response:
                item["_id"] = str(item["_id"])    
            
            return JSONResponse(content={"data": response})
        
        except Exception as e:
            self.log_error("Error fetching sensor data", e)
            return JSONResponse(
                content={"error": "Failed to retrieve sensor data", "details": str(e)},
                status_code=500
            )

    async def get_data_for_display(self, date=None):
        """
        Get processed sensor data for dashboard display
        
        Args:
            date: Date string in format YYYY/MM/DD (defaults to today if None)
            
        Returns:
            JSONResponse with processed data or error message
        """
        try:
            # Default to today's date if none is provided
            if not date:
                date = datetime.now().strftime("%Y/%m/%d")
            
            # Extract the month and year from the given date
            try:
                parsed_date = datetime.strptime(date, "%Y/%m/%d")
                end_date = parsed_date
                start_date = end_date - timedelta(days=30)
            except ValueError:
                return JSONResponse(
                    content={"error": "Invalid date format. Use YYYY/MM/DD."}, 
                    status_code=400
                )
            
            # Query MongoDB for data within the date range
            response = list(self.db_farm.find({
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
                
                daily_averages_df.columns = [
                    'date', 
                    'temperature_average', 'temperature_max', 'temperature_min',
                    'humidity_average', 'humidity_max', 'humidity_min',
                    'EC_average', 'EC_max', 'EC_min'
                ]
                
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

            # Return the required data as dictionaries
            return JSONResponse(
                content={
                    "current_date_data": current_date_data,
                    "latest_data_entries": latest_data_entries,
                    "min_max_values": min_max_values,
                    "monthly_daily_averages": monthly_daily_averages,
                }
            )
            
        except Exception as e:
            self.log_error("Error processing data for display", e)
            return JSONResponse(
                content={"error": "Failed to process sensor data for display", "details": str(e)},
                status_code=500
            )

    async def get_data_range(self, start_date, end_date, device_id):
        """
        Get sensor data within a date range for a specific device
        
        Args:
            start_date: Start date string in format YYYY/MM/DD
            end_date: End date string in format YYYY/MM/DD
            device_id: Device identifier
            
        Returns:
            JSONResponse with data or error message
        """
        try:
            if not start_date or not end_date or not device_id:
                return JSONResponse(
                    content={"error": "start_date, end_date, and device_id are all required"},
                    status_code=400
                )
                
            start_datetime = datetime.strptime(start_date, "%Y/%m/%d")
            end_datetime = datetime.strptime(end_date, "%Y/%m/%d") + timedelta(days=1) - timedelta(seconds=1)

            response = list(self.db_farm.find({
                "time": {
                    "$gte": start_datetime.strftime("%Y/%m/%d"),
                    "$lte": end_datetime.strftime("%Y/%m/%d %H:%M:%S")
                },
                "id": device_id
            }))

            for item in response:
                item["_id"] = str(item["_id"])

            return JSONResponse(content={"data": response})

        except Exception as e:
            self.log_error("Error retrieving data range", e)
            return JSONResponse(
                content={"error": "Failed to retrieve sensor data range", "details": str(e)},
                status_code=500
            )

    async def add_data(self, data):
        """
        Add new sensor data to the database
        
        Args:
            data: Sensor data to be saved
            
        Returns:
            JSONResponse indicating success or failure
        """
        try:
            # Log the incoming data
            self.db_logs.insert_one({"type": "data", "message": str(data)})
            
            # Insert data into the farm database
            result = self.db_farm.insert_one(data)
            
            return JSONResponse(
                content={"success": True, "id": str(result.inserted_id)},
                status_code=201
            )
            
        except Exception as e:
            self.log_error("Error saving sensor data", e)
            # Still try to log the error even if the main operation failed
            try:
                self.db_logs.insert_one({"type": "error", "message": str(e)})
            except:
                pass  # Already logged in log_error
                
            return JSONResponse(
                content={"success": False, "error": "Failed to save sensor data", "details": str(e)},
                status_code=500
            )