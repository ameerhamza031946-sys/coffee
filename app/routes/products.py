from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Any
from bson import ObjectId

from app.database import get_database
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductDb
from app.auth.dependencies import get_current_admin

router = APIRouter(prefix="/products", tags=["products"])

@router.get("/", response_model=List[ProductResponse])
async def get_products(db: AsyncIOMotorDatabase = Depends(get_database)) -> Any:
    products_cursor = db["products"].find()
    products = await products_cursor.to_list(length=100)
    for p in products:
        p["id"] = str(p.pop("_id"))
    return products

@router.get("/{id}", response_model=ProductResponse)
async def get_product(id: str, db: AsyncIOMotorDatabase = Depends(get_database)) -> Any:
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    product = await db["products"].find_one({"_id": ObjectId(id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product["id"] = str(product.pop("_id"))
    return product

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate, 
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_admin: dict = Depends(get_current_admin)
) -> Any:
    new_product = ProductDb(**product.model_dump())
    result = await db["products"].insert_one(new_product.model_dump(by_alias=True, exclude={"id"}))
    created_product = await db["products"].find_one({"_id": result.inserted_id})
    created_product["id"] = str(created_product.pop("_id"))
    return created_product

@router.put("/{id}", response_model=ProductResponse)
async def update_product(
    id: str, 
    product_update: ProductUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_admin: dict = Depends(get_current_admin)
) -> Any:
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
        
    update_data = {k: v for k, v in product_update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
        
    result = await db["products"].update_one(
        {"_id": ObjectId(id)},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
        
    updated_product = await db["products"].find_one({"_id": ObjectId(id)})
    updated_product["id"] = str(updated_product.pop("_id"))
    return updated_product

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_admin: dict = Depends(get_current_admin)
):
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
        
    result = await db["products"].delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return None
