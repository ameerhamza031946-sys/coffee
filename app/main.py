from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

from app.database import db, settings
from app.routes import auth, products, cart, orders

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.utils.rate_limit import limiter

app = FastAPI(title="Coffee Website API", version="1.0.0")

# Add Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    print("Connected to the MongoDB database!")
    
    # Database seeding
    database = db.client.coffee_db
    
    # 1. Seed Admin user if not exists
    admin_user = await database["users"].find_one({"email": "admin"})
    if not admin_user:
        from app.auth.security import get_password_hash
        await database["users"].insert_one({
            "email": "admin",
            "username": "Admin",
            "hashed_password": get_password_hash("coffee123"),
            "role": "admin"
        })
        print("Admin user seeded.")
        
    # 2. Seed default products if products collection is empty
    product_count = await database["products"].count_documents({})
    if product_count == 0:
        default_products = [
            {
                "name": "Classic Espresso",
                "price": 3.50,
                "desc": "Rich, bold, and full-bodied single-origin espresso.",
                "emoji": "☕",
                "cat": "Hot Coffee",
                "stock": 50
            },
            {
                "name": "Caramel Macchiato",
                "price": 4.80,
                "desc": "Steamed milk with vanilla-flavored syrup, marked with espresso and caramel.",
                "emoji": "🍯",
                "cat": "Hot Coffee",
                "stock": 40
            },
            {
                "name": "Artisan Latte",
                "price": 4.50,
                "desc": "A smooth blend of double espresso and velvety steamed milk.",
                "emoji": "🥛",
                "cat": "Hot Coffee",
                "stock": 45
            },
            {
                "name": "Nitro Cold Brew",
                "price": 5.00,
                "desc": "Slow-steeped cold brew infused with nitrogen for a rich, creamy head.",
                "emoji": "🧊",
                "cat": "Cold Coffee",
                "stock": 30
            },
            {
                "name": "Iced Caramel Latte",
                "price": 4.90,
                "desc": "Chilled espresso and milk poured over ice, sweetened with caramel syrup.",
                "emoji": "🥤",
                "cat": "Cold Coffee",
                "stock": 35
            },
            {
                "name": "Butter Croissant",
                "price": 3.00,
                "desc": "Flaky, golden-brown French pastry made with pure butter.",
                "emoji": "🥐",
                "cat": "Desserts",
                "stock": 20
            },
            {
                "name": "Decadent Fudge Cake",
                "price": 5.50,
                "desc": "Rich chocolate layer cake filled and frosted with dark chocolate fudge.",
                "emoji": "🍰",
                "cat": "Desserts",
                "stock": 15
            }
        ]
        await database["products"].insert_many(default_products)
        print("Default products seeded.")


@app.on_event("shutdown")
async def shutdown_db_client():
    db.client.close()
    print("Closed MongoDB connection.")

# Include routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)

@app.get("/db-debug")
async def db_debug():
    try:
        from app.database import get_database
        database = db.client.coffee_db
        collections = await database.list_collection_names()
        # Get MONGODB_URL from settings (masking credentials)
        url = settings.MONGODB_URL
        masked_url = url
        if "@" in url:
            parts = url.split("@")
            masked_url = "mongodb+srv://***:***@" + parts[-1]
        return {
            "database_name": "coffee_db",
            "collections": collections,
            "masked_mongodb_url": masked_url,
            "client_initialized": db.client is not None
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def root():
    return {"message": "Welcome to the Coffee Website API. Go to /docs for the API documentation."}

