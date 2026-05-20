from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Any
from bson import ObjectId
from datetime import datetime

from app.database import get_database
from app.schemas.order import OrderCreate, OrderResponse, OrderResponseDb
from app.auth.dependencies import get_current_active_user, get_current_admin
from app.routes.cart import get_or_create_cart

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def place_order(
    order_data: OrderCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_active_user)
) -> Any:
    user_id = str(current_user["_id"])
    cart = await get_or_create_cart(user_id, db)
    
    if not cart.get("items"):
        raise HTTPException(status_code=400, detail="Cart is empty")
        
    # Calculate total price (simplified, assuming we have product info or just query it)
    total_price = 0.0
    for item in cart["items"]:
        product = await db["products"].find_one({"_id": ObjectId(item["product_id"])})
        if product:
            total_price += product.get("price", 0.0) * item["quantity"]
            
    # Create order
    new_order = OrderResponseDb(
        user_id=user_id,
        items=cart["items"],
        total_price=total_price,
        shipping_address=order_data.shipping_address,
        status="pending"
    )
    
    result = await db["orders"].insert_one(new_order.model_dump(by_alias=True, exclude={"id"}))
    
    # Clear cart
    await db["carts"].update_one(
        {"_id": cart["_id"]},
        {"$set": {"items": []}}
    )
    
    created_order = await db["orders"].find_one({"_id": result.inserted_id})
    created_order["id"] = str(created_order.pop("_id"))
    return created_order

@router.get("/my-orders", response_model=List[OrderResponse])
async def get_my_orders(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_active_user)
) -> Any:
    user_id = str(current_user["_id"])
    cursor = db["orders"].find({"user_id": user_id})
    orders = await cursor.to_list(length=100)
    for o in orders:
        o["id"] = str(o.pop("_id"))
    return orders

@router.get("/all", response_model=List[OrderResponse])
async def get_all_orders(
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_admin: dict = Depends(get_current_admin)
) -> Any:
    cursor = db["orders"].find()
    orders = await cursor.to_list(length=1000)
    for o in orders:
        o["id"] = str(o.pop("_id"))
    return orders
