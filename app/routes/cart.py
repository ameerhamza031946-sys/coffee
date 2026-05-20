from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Any
from bson import ObjectId

from app.database import get_database
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartResponse, CartDb
from app.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/cart", tags=["cart"])

async def get_or_create_cart(user_id: str, db: AsyncIOMotorDatabase) -> dict:
    cart = await db["carts"].find_one({"user_id": user_id})
    if not cart:
        new_cart = CartDb(user_id=user_id, items=[])
        result = await db["carts"].insert_one(new_cart.model_dump(by_alias=True, exclude={"id"}))
        cart = await db["carts"].find_one({"_id": result.inserted_id})
    return cart

@router.get("/", response_model=CartResponse)
async def get_cart(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_active_user)
) -> Any:
    user_id = str(current_user["_id"])
    cart = await get_or_create_cart(user_id, db)
    cart["id"] = str(cart.pop("_id"))
    return cart

@router.post("/items", response_model=CartResponse)
async def add_item_to_cart(
    item: CartItemCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_active_user)
) -> Any:
    user_id = str(current_user["_id"])
    cart = await get_or_create_cart(user_id, db)
    
    # Check if item already in cart
    existing_item = next((i for i in cart["items"] if i["product_id"] == item.product_id), None)
    
    if existing_item:
        await db["carts"].update_one(
            {"_id": cart["_id"], "items.product_id": item.product_id},
            {"$inc": {"items.$.quantity": item.quantity}}
        )
    else:
        await db["carts"].update_one(
            {"_id": cart["_id"]},
            {"$push": {"items": item.model_dump()}}
        )
        
    updated_cart = await db["carts"].find_one({"_id": cart["_id"]})
    updated_cart["id"] = str(updated_cart.pop("_id"))
    return updated_cart

@router.put("/items/{product_id}", response_model=CartResponse)
async def update_cart_item(
    product_id: str,
    item_update: CartItemUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_active_user)
) -> Any:
    user_id = str(current_user["_id"])
    cart = await get_or_create_cart(user_id, db)
    
    result = await db["carts"].update_one(
        {"_id": cart["_id"], "items.product_id": product_id},
        {"$set": {"items.$.quantity": item_update.quantity}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found in cart")
        
    updated_cart = await db["carts"].find_one({"_id": cart["_id"]})
    updated_cart["id"] = str(updated_cart.pop("_id"))
    return updated_cart

@router.delete("/items/{product_id}", response_model=CartResponse)
async def remove_item_from_cart(
    product_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_active_user)
) -> Any:
    user_id = str(current_user["_id"])
    cart = await get_or_create_cart(user_id, db)
    
    await db["carts"].update_one(
        {"_id": cart["_id"]},
        {"$pull": {"items": {"product_id": product_id}}}
    )
    
    updated_cart = await db["carts"].find_one({"_id": cart["_id"]})
    updated_cart["id"] = str(updated_cart.pop("_id"))
    return updated_cart
