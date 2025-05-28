from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, UTC
from bson import ObjectId

class LedgerEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    coa_id: str = Field(..., description="ID of the related Chart of Account")
    transaction_date: datetime = Field(..., description="Date of the transaction")
    description: str = Field(..., description="Description of the transaction")
    debit_amount: float = Field(default=0.0, description="Debit amount")
    credit_amount: float = Field(default=0.0, description="Credit amount")
    reference_number: Optional[str] = Field(None, description="Reference number for the transaction")
    notes: Optional[str] = Field(None, description="Additional notes")
    created_by: str = Field(..., description="User who created the entry")
    created_dt: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_by: Optional[str] = Field(None, description="User who last updated the entry")
    updated_dt: Optional[datetime] = Field(None, description="Last update timestamp")
    is_active: bool = Field(default=True, description="Whether the entry is active")

class LedgerUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_date: Optional[datetime] = None
    description: Optional[str] = None
    debit_amount: Optional[float] = None
    credit_amount: Optional[float] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    updated_by: Optional[str] = None
    is_active: Optional[bool] = None 