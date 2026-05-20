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

@app.on_event("shutdown")
async def shutdown_db_client():
    db.client.close()
    print("Closed MongoDB connection.")

# Include routers
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Coffee Website API. Go to /docs for the API documentation."}
