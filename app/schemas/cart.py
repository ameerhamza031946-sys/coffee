from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.user import PyObjectId

class CartItemBase(BaseModel):
    product_id: str
    quantity: int = Field(default=1, gt=0)

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)

class CartItemResponse(CartItemBase):
    pass # we might want to attach product details, but ID and quantity is fine for simple cart

class CartDb(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: str
    items: List[CartItemBase] = []
    
    class Config:
        populate_by_name = True

class CartResponse(BaseModel):
    id: str
    user_id: str
    items: List[CartItemResponse]
