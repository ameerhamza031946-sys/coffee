from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.user import PyObjectId

class ProductBase(BaseModel):
    name: str
    price: float
    description: str
    image_url: str

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    image_url: Optional[str] = None

class ProductResponse(ProductBase):
    id: str

class ProductDb(ProductBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    
    class Config:
        populate_by_name = True
