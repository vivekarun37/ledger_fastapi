from bson import ObjectId
from pymongo.errors import PyMongoError
from fastapi import HTTPException, status
from jitfarm_api.models.farmModel import CustomField, FieldTemplate
from datetime import datetime
import json
from typing import List, Dict, Any, Optional

class FieldTemplateService:
    def __init__(self, db_client):
        self.collection = db_client.npk.field_templates 

    async def get_field_templates(self, client_id: str, applies_to: Optional[str] = None):
        """Get all active field templates for a specific client"""
        query = {"isActive": True, "client_id": client_id}
        
        # Filter by where this field can be applied
        if applies_to:
            query["applies_to"] = applies_to
            
        templates = self.collection.find(query).to_list(1000)
        return [self._process_template(template) for template in templates]

    async def get_field_template(self, template_id: str):
        """Get a specific field template by ID"""
        try:
            obj_id = ObjectId(template_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid ID format")
        
        template = self.collection.find_one({"_id": obj_id})
        if not template:
            raise HTTPException(status_code=404, detail="Field template not found")
        
        return self._process_template(template)

    async def create_field_templates(self, client_id: str, templates: List[FieldTemplate]):
        """Create or update multiple field templates for a client"""
        result = {"created": 0, "updated": 0}
        
        for template_data in templates:
            template_dict = template_data.dict(exclude_unset=True)
            # Ensure client_id is set
            template_dict["client_id"] = client_id
            now = datetime.utcnow()

            if template_data.id:
                try:
                    obj_id = ObjectId(template_data.id)
                    update_result = self.collection.update_one(
                        {"_id": obj_id, "client_id": client_id},  # Ensure client ownership
                        {"$set": {**template_dict, "updated_at": now}}
                    )

                    if update_result.modified_count:
                        result["updated"] += 1
                        continue
                except:
                    pass  
            
            template_dict.pop("id", None)
            new_template = {
                **template_dict,
                "created_at": now,
                "updated_at": now
            }

            result_insert = self.collection.insert_one(new_template)
            if result_insert.inserted_id:
                result["created"] += 1
        
        return result

    async def update_field_template(self, client_id: str, template_id: str, template: dict):
        """Update a specific field template for a client"""
        try:
            obj_id = ObjectId(template_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid ID format")
        
        template["updated_at"] = datetime.utcnow()
        
        update_result = self.collection.update_one(
            {"_id": obj_id, "client_id": client_id},  # Ensure client ownership
            {"$set": template}
        )

        if update_result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Field template not found or not authorized")

        updated_template =self.collection.find_one({"_id": obj_id})
        return self._process_template(updated_template)

    async def delete_field_template(self, client_id: str, template_id: str):
        """Soft delete a field template by setting isActive to false"""
        try:
            obj_id = ObjectId(template_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid ID format")

        update_result = self.collection.update_one(
            {"_id": obj_id, "client_id": client_id},  # Ensure client ownership
            {"$set": {"isActive": False, "updated_at": datetime.utcnow()}}
        )

        if update_result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Field template not found or not authorized")

        return {"status": "success", "message": "Field template deleted successfully"}

    def _process_template(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """Process a template from MongoDB to return in API response"""
        return {
            "id": str(template["_id"]),
            "client_id": template["client_id"],
            "name": template["name"],
            "type": template["type"],
            "options": template.get("options", []),
            "applies_to": template.get("applies_to", ["crop", "planting"]),
            "isActive": template["isActive"],
            "created_at": template["created_at"],
            "updated_at": template["updated_at"]
        }