# File: schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional

# --- Pydantic Models for Data Structure ---

class InvoiceItem(BaseModel):
    description: str = Field(..., description="Description of the item purchased")
    quantity: Optional[str] = Field(None, description="Quantity of items")
    unit_price: Optional[str] = Field(None, description="Price per unit")
    total_price: Optional[str] = Field(None, description="Total price for this line item")

class VendorInfo(BaseModel):
    name_english: Optional[str] = None
    name_nepali: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    vat_number: Optional[str] = None

class CustomerInfo(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    vat_number: Optional[str] = None

class Summary(BaseModel):
    subtotal: Optional[str] = None
    tax_amount: Optional[str] = None
    tax_rate_percent: Optional[str] = None
    discount_amount: Optional[str] = None
    total_amount_due: Optional[str] = None
    amount_in_words: Optional[str] = None
    has_company_stamp: str = Field(..., description="Yes or No")

class InvoiceData(BaseModel):
    invoice_number: Optional[str] = None
    transaction_number: Optional[str] = None
    reference_number: Optional[str] = None
    invoice_date_ad: Optional[str] = Field(None, description="YYYY-MM-DD")
    invoice_miti_bs: Optional[str] = Field(None, description="YYYY-MM-DD")
    vendor_info: VendorInfo
    customer_info: CustomerInfo
    line_items: List[InvoiceItem]
    summary: Summary