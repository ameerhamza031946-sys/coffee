from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.schemas.user import PyObjectId
from app.schemas.cart import CartItemBase

class OrderCreate(BaseModel):
    # Depending on requirements, we might just checkout the cart, meaning no body required.
    # We will provide an empty model or delivery address, etc.
    shipping_address: str

class OrderResponseDb(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: str
    items: List[CartItemBase]
    total_price: float
    shipping_address: str
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

class OrderResponse(BaseModel):
    id: str
    user_id: str
    items: List[CartItemBase]
    total_price: float
    shipping_address: str
    status: str
    created_at: datetime
