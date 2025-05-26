from bson import ObjectId
from pymongo.errors import PyMongoError
from fastapi import HTTPException, status
from models.farmModel import Contacts
from typing import List, Dict, Any, Optional
from datetime import datetime

class ContactService:
    def __init__(self, db_client):
        self.db_client = db_client
        self.contacts_collection = db_client.contacts
        self.countries_collection = db_client.countries_db

    async def add_contact(self, contact: Contacts) -> Dict[str, str]:
        try:
            contact_data = contact.dict()
            result = self.contacts_collection.insert_one(contact_data)
            return {
                "status": "success",
                "message": "Contact added successfully",
                "id": str(result.inserted_id)
            }
        except PyMongoError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}"
            )

    async def get_contacts(self, client_id: str) -> List[Dict[str, Any]]:
        try:
            contacts = self.contacts_collection.find({"client_id": client_id}).to_list(length=100)
            
            for contact in contacts:
                contact["_id"] = str(contact["_id"])
                
            return contacts
        except PyMongoError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}"
            )

    async def update_contact(self, contact_id: str, contact: Contacts) -> Dict[str, str]:
        """
        Update an existing contact
        """
        try:
            if not ObjectId.is_valid(contact_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Invalid contact ID format"
                )

            existing_contact = self.contacts_collection.find_one({"_id": ObjectId(contact_id)})
            
            if not existing_contact:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail="Contact not found"
                )

            update_data = {
                "client_id": existing_contact["client_id"],
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "email": contact.email,
                "contact_type": contact.contact_type,
                "ph_no": contact.ph_no,
                "company": contact.company,
                "country": contact.country,
                "state": contact.state,
                "city": contact.city,
                "address": contact.address,
                "postal_code": contact.postal_code,
                "created_dt": contact.created_dt,
                "created_by": contact.created_by,
                "updated_dt": datetime.now(), 
                "updated_by": contact.updated_by
            }

            result = self.contacts_collection.update_one(
                {"_id": ObjectId(contact_id)}, 
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                pass
                
            return {
                "status": "success",
                "message": "Contact updated successfully",
            }
        except HTTPException as e:
            raise e
        except PyMongoError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}"
            )

    async def delete_contact(self, contact_id: str) -> Dict[str, str]:
        """
        Delete a contact
        """
        try:
            if not ObjectId.is_valid(contact_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Invalid contact ID format"
                )

            contact_record = self.contacts_collection.find_one({"_id": ObjectId(contact_id)})
            
            if not contact_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail="Contact not found"
                )
                
            result = self.contacts_collection.delete_one({"_id": ObjectId(contact_id)})
            
            if result.deleted_count == 0:
                pass
            return {
                "status": "success",
                "message": "Contact deleted successfully",
            }
        except HTTPException as e:
            raise e
        except PyMongoError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}"
            )

    async def get_countries(self) -> Dict[str, Any]:
        """
        Get countries data
        """
        try:
            country = self.countries_collection.find_one({"id": 101})
            
            if not country:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Country with id 101 not found"
                )
                
            country["_id"] = str(country["_id"])
            
            return country
        except PyMongoError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database error: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}"
            )