from bson import ObjectId
from fastapi import HTTPException, status
from pymongo.errors import PyMongoError
from jitfarm_api.models.farmModel import Form, Field
from datetime import datetime
from typing import Dict, List, Optional, Any
import json

class FormService:
    def __init__(self, db_client):
        """
        Initialize the form service with a database client
        
        Args:
            db_client: MongoDB client with form collections
        """
        self.db_form_fields = db_client.formFields
        self.db_form_data = db_client.form_data
        self.db = db_client

    async def delete_form(self, form_id: str) -> Dict[str, str]:
        """
        Delete a form configuration by ID
        
        Args:
            form_id: ID of the form to delete
            
        Returns:
            Dictionary with status and message
            
        Raises:
            ValueError: If input validation fails
            PyMongoError: If database operation fails
            Exception: For other unexpected errors
        """
        if not ObjectId.is_valid(form_id):
            raise ValueError("Invalid form ID format")
                
        del_record = self.db_form_fields.delete_one({"_id": ObjectId(form_id)})
        
        if del_record.deleted_count > 0:
            return {
                "status": "success",
                "message": "Form deleted successfully"
            }
        else:
            return {
                "status": "error",
                "message": "Form not found"
            }

    async def delete_form_data(self, form_id: str) -> Dict[str, str]:
        """
        Delete form data by ID
        
        Args:
            form_id: ID of the form data to delete
            
        Returns:
            Dictionary with status and message
            
        Raises:
            ValueError: If input validation fails
            PyMongoError: If database operation fails
            Exception: For other unexpected errors
        """
        if not ObjectId.is_valid(form_id):
            raise ValueError("Invalid form ID format")
                
        del_record = self.db_form_data.delete_one({"_id": ObjectId(form_id)})
        
        if del_record.deleted_count > 0:
            return {
                "status": "success",
                "message": "Form data deleted successfully"
            }
        else:
            return {
                "status": "error",
                "message": "Form data not found"
            }

    async def get_form(self, stage: str, client_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a form by stage and optionally by client ID
        
        Args:
            stage: Stage of the form to retrieve
            client_id: Optional client ID to filter forms
            
        Returns:
            Dictionary with status, message, and form data
            
        Raises:
            PyMongoError: If database operation fails
            Exception: For other unexpected errors
        """
        if not stage:
            return {"status": "fail", "message": "Stage parameter is required"}

        # Build query with stage, add client_id if provided
        query = {"stage": stage}
        if client_id:
            query["client_id"] = client_id

        # Retrieve the form for the given stage and client
        form = self.db_form_fields.find_one(query)
        
        if form:
            # Convert ObjectId to string for JSON serialization
            if "_id" in form:
                form["_id"] = str(form["_id"])
            # Convert datetime objects to ISO format strings
            if "created_dt" in form and isinstance(form["created_dt"], datetime):
                form["created_dt"] = form["created_dt"].isoformat()
            if "updated_dt" in form and isinstance(form["updated_dt"], datetime):
                form["updated_dt"] = form["updated_dt"].isoformat()
                
            return {
                "status": "success",
                "message": "Form found",
                "form": form
            }
        else:
            return {"status": "fail", "message": "Form not found for the specified criteria"}

    async def add_form_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add form data to the database
        
        Args:
            data: Form data to add
            
        Returns:
            Dictionary with status, message, and ID
            
        Raises:
            ValueError: If required fields are missing
            PyMongoError: If database operation fails
            Exception: For other unexpected errors
        """
        # Validate required fields according to Form model
        required_keys = {"client_id", "stage", "fields", "created_by", "updated_by"}
        if not required_keys.issubset(data.keys()):
            missing_keys = required_keys - data.keys()
            raise ValueError(f"Missing required keys: {missing_keys}")
            
        # Handle datetime conversions
        if "created_dt" in data and isinstance(data["created_dt"], str):
            try:
                data["created_dt"] = datetime.fromisoformat(data["created_dt"])
            except ValueError:
                data["created_dt"] = datetime.utcnow()
        else:
            data["created_dt"] = datetime.utcnow()
            
        if "updated_dt" in data and isinstance(data["updated_dt"], str):
            try:
                data["updated_dt"] = datetime.fromisoformat(data["updated_dt"])
            except ValueError:
                data["updated_dt"] = datetime.utcnow()
        else:
            data["updated_dt"] = datetime.utcnow()
            
        # Remove _id if present to ensure it's a new insertion
        if "_id" in data:
            del data["_id"]

        # Check if a form for this stage and client already exists in formFields
        existing_form = self.db_form_fields.find_one({
            "stage": data["stage"],
            "client_id": data["client_id"]
        })
        
        if existing_form:
            # If the form already exists, update it
            result = self.db_form_fields.update_one(
                {"_id": existing_form["_id"]},
                {"$set": data}
            )
            
            return {
                "status": "success", 
                "message": "Form updated successfully.", 
                "id": str(existing_form["_id"])
            }
        else:
            # Insert the new form into formFields collection
            response = self.db_form_fields.insert_one(data)

            # Return success response
            return {
                "status": "success", 
                "message": "Form created successfully.", 
                "id": str(response.inserted_id)
            }

    async def update_form_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update existing form data
        
        Args:
            data: Form data with _id to update
            
        Returns:
            Dictionary with status, message, and ID
            
        Raises:
            ValueError: If required fields are missing
            PyMongoError: If database operation fails
            Exception: For other unexpected errors
        """
        # Validate required fields
        if "_id" not in data:
            raise ValueError("Form ID is required for update")
            
        if "stage" not in data or "fields" not in data or "client_id" not in data:
            raise ValueError("Stage, fields, and client_id are required")
            
        if "updated_by" not in data:
            raise ValueError("Updated_by field is required")

        form_id = data["_id"]
        if not ObjectId.is_valid(form_id):
            raise ValueError("Invalid form ID format")
            
        # Convert string ID to ObjectId
        object_id = ObjectId(form_id)
        
        # Remove _id from data for update operation
        update_data = {k: v for k, v in data.items() if k != "_id"}
        
        # Handle updated_dt conversion
        if "updated_dt" in update_data and isinstance(update_data["updated_dt"], str):
            try:
                update_data["updated_dt"] = datetime.fromisoformat(update_data["updated_dt"])
            except ValueError:
                update_data["updated_dt"] = datetime.utcnow()
        else:
            update_data["updated_dt"] = datetime.utcnow()
        
        # Update the form
        result = self.db_form_fields.update_one(
            {"_id": object_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            return {
                "status": "fail",
                "message": "Form not found"
            }
            
        if result.modified_count == 0:
            return {
                "status": "success",
                "message": "No changes applied to the form",
                "id": form_id
            }
            
        return {
            "status": "success",
            "message": "Form updated successfully",
            "id": form_id
        }

    async def get_form_data(
        self,
        stage: Optional[str] = None,
        client_id: Optional[str] = None,
        created_by: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get form data with optional filters
        
        Args:
            stage: Filter by stage
            client_id: Filter by client ID
            created_by: Filter by creator
            limit: Number of records to retrieve
            offset: Number of records to skip
            
        Returns:
            Dictionary with status, data, and count
            
        Raises:
            PyMongoError: If database operation fails
            Exception: For other unexpected errors
        """
        # Build the query based on optional filters
        query = {}
        if stage:
            query["stage"] = stage
        if client_id:
            query["client_id"] = client_id
        if created_by:
            query["created_by"] = created_by

        # Retrieve data from MongoDB with filters, limit, and offset
        cursor = self.db_form_data.find(query).skip(offset).limit(limit)
        stage_data = {}

        # Process documents from the cursor
        for document in cursor:
            document["_id"] = str(document["_id"])  # Convert ObjectId to string
            
            # Convert datetime objects to strings
            if "created_dt" in document and isinstance(document["created_dt"], datetime):
                document["created_dt"] = document["created_dt"].isoformat()
            if "updated_dt" in document and isinstance(document["updated_dt"], datetime):
                document["updated_dt"] = document["updated_dt"].isoformat()
                
            stage_name = document.get("stage", "Unknown")
            if stage_name not in stage_data:
                stage_data[stage_name] = []
            stage_data[stage_name].append(document)

        # Format the response
        response_data = [
            {"stage": stage_name, "data": data_list}
            for stage_name, data_list in stage_data.items()
        ]

        return {
            "status": "success",
            "data": response_data,
            "count": sum(len(data_list) for data_list in stage_data.values()),
        }
        
    async def get_forms_by_client(self, client_id: str) -> Dict[str, Any]:
        """
        Get all forms for a specific client
        
        Args:
            client_id: Client ID to filter forms
            
        Returns:
            Dictionary with status, message, and forms
            
        Raises:
            PyMongoError: If database operation fails
            Exception: For other unexpected errors
        """
        if not client_id:
            return {"status": "fail", "message": "Client ID is required"}
            
        # Retrieve all forms for the given client ID
        cursor = self.db_form_fields.find({"client_id": client_id})
        forms = []
        
        for form in cursor:
            # Convert ObjectId to string
            if "_id" in form:
                form["_id"] = str(form["_id"])
                
            # Convert datetime objects to strings
            if "created_dt" in form and isinstance(form["created_dt"], datetime):
                form["created_dt"] = form["created_dt"].isoformat()
            if "updated_dt" in form and isinstance(form["updated_dt"], datetime):
                form["updated_dt"] = form["updated_dt"].isoformat()
                
            forms.append(form)
            
        if forms:
            return {
                "status": "success",
                "message": "Forms retrieved successfully",
                "forms": forms
            }
        else:
            return {"status": "fail", "message": "No forms found for the specified client"}

    async def get_stages(self, client_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get distinct form stages, optionally filtered by client ID
        
        Args:
            client_id: Optional client ID to filter stages
            
        Returns:
            Dictionary with status, message and stages
            
        Raises:
            PyMongoError: If database operation fails
            Exception: For other unexpected errors
        """
        # Apply client_id filter if provided
        query = {}
        if client_id:
            query["client_id"] = client_id
            
        # Retrieve distinct stages with optional filter
        stages = self.db_form_fields.distinct("stage", query)

        if stages:
            return {
                "status": "success",
                "message": "Stages retrieved successfully",
                "stages": stages
            }
        else:
            return {"status": "fail", "message": "No stages found for the specified criteria"}