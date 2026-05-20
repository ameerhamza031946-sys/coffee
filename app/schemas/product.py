from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.user import PyObjectId

class ProductBase(BaseModel):
    name: str
    price: float
    desc: str = "Delicious item"
    emoji: Optional[str] = "☕"
    cat: str = "Hot Coffee"
    stock: int = 0

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    desc: Optional[str] = None
    emoji: Optional[str] = None
    cat: Optional[str] = None
    stock: Optional[int] = None

class ProductResponse(ProductBase):
    id: str

class ProductDb(ProductBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    
    class Config:
        populate_by_name = True
