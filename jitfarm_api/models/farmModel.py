from pydantic import BaseModel
from typing import Dict ,List, Optional, Any
from datetime import datetime


class SensorData(BaseModel):
    id : str
    time: str
    humidity: float
    temperature: float
    EC: float
    PH: float
    N: float
    P: float
    K: float
    power: float


class Field(BaseModel):
    label: str = "default_label"
    type: str = "text"
    required: bool = True

class Form(BaseModel):
    client_id: str
    stage: str
    fields: Dict[str, Field]
    created_by :str
    created_dt : datetime = Field(default_factory=datetime.utcnow)
    updated_by :str
    updated_dt : datetime = Field(default_factory=datetime.utcnow)

class CustomField(BaseModel):
    template_id: str
    name: str
    type: str
    value: Any = None
    options: Optional[List[str]] = []

class FieldTemplate(BaseModel):
    id: Optional[str] = None
    client_id: str
    name: str
    type: str 
    options: Optional[List[str]] = []
    isActive: bool = True
    applies_to: List[str] = ["crop", "planting"] 
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Clients(BaseModel):
    name: str
    description: str
    client_code: str
    created_by :str
    created_dt : datetime = Field(default_factory=datetime.utcnow)
    updated_by :str
    updated_dt : datetime = Field(default_factory=datetime.utcnow)
    

class Device(BaseModel):
    device_name: str
    device_type: str
    device_id: str
    client_id: str
    description: str
    created_by :str
    is_active : bool = False
    created_dt : datetime = Field(default_factory=datetime.utcnow)
    updated_by :str
    updated_dt : datetime = Field(default_factory=datetime.utcnow)

class Crops(BaseModel):
    crop_name: str
    crop_variety: str
    crop_id: Optional[str] = None
    client_id: str
    planting_data: Dict = Field(default_factory=dict)
    harvest_data: Dict = Field(default_factory=dict)
    custom_fields: List[CustomField] = Field(default_factory=list)
    tasks: List[Dict] = Field(default_factory=list)
    created_by :str
    created_dt : datetime = Field(default_factory=datetime.utcnow)
    updated_by :str
    updated_dt : datetime = Field(default_factory=datetime.utcnow)

class FieldDetails(BaseModel):
    planting_data: Dict = Field(default_factory=dict)
    harvest_data: Dict = Field(default_factory=dict)
    custom_fields: List[CustomField] = Field(default_factory=list)
    

class Fields(BaseModel):
    client_id: str
    name: str
    planting_format: str
    number_of_beds: Optional[int] = None
    bed_length: Optional[float] = None
    bed_width: Optional[float] = None
    area_size: Optional[float] = None
    estimated_land_value: Optional[float] = None
    status: str
    light_profile: Optional[str] = None
    rest_days: Optional[int] = None
    location_type: str
    field_details: FieldDetails = Field(default_factory=FieldDetails)
    device_data: Dict = Field(default_factory=dict)
    created_dt: Optional[str] = None
    updated_dt: Optional[str] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

class Contacts(BaseModel):
    client_id: Optional[str] = None
    first_name: str
    last_name: str
    email: str
    contact_type: str
    ph_no: str
    company: str
    country: str
    address: str
    city: str
    state: str
    postal_code: str
    created_by :str
    created_dt : datetime = Field(default_factory=datetime.utcnow)
    updated_by :str
    updated_dt : datetime = Field(default_factory=datetime.utcnow)


class RolePermission(BaseModel):
    read: bool = False
    create: bool = False
    update: bool = False
    delete: bool = False

class Role(BaseModel):
    name: str
    description: str
    client_id: Optional[str] = None
    permissions: Dict[str, RolePermission]
    is_system_generated: bool = False
    created_by: Optional[str] = None
    created_dt: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_dt: Optional[datetime] = None

class Users(BaseModel):
    user_name: str 
    password: str 
    email: str
    client_id: str
    role_permissions: Optional[Dict] = None
    roles: Optional[List[str]] = []
    role_names: Optional[List[str]] = []
    role: Optional[str] = None
    role_name: Optional[str] = None
    is_system_generated: bool = False
    created_by: str
    created_dt: datetime = Field(default_factory=datetime.utcnow)
    updated_by: str
    updated_dt: datetime = Field(default_factory=datetime.utcnow)

class UserLogin(BaseModel):
    user_name: str
    password: str

class COAccount(BaseModel):
    account_name: str
    account_code: str
    account_type: str 
    account_subtype: str
    account_number: Optional[str]= None
    description: str
    is_active: bool
    is_group: bool = False
    parent_id: Optional[str] = None
    children: Optional[List[Dict[str, Any]]] = []
    client_id: str
    created_by: str
    created_dt: str = Field(default_factory=datetime.utcnow)
    updated_by: str
    updated_dt: str = Field(default_factory=datetime.utcnow)

class Transaction(BaseModel):
    client_id: str
    transaction_type: str 
    amount: float
    date: str 
    payee: str
    category: str 
    category_name: Optional[str] = None
    check_number: Optional[str] = None
    reporting_year: Optional[str] = None
    associated_to: Optional[str] = None 
    keywords: Optional[str] = None
    description: Optional[str] = None
    created_by: str
    created_dt: str = Field(default_factory=datetime.utcnow)
    updated_by: str
    updated_dt: str = Field(default_factory=datetime.utcnow)
