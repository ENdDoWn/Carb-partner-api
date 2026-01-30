from controllers import partner_controller
from contextlib import asynccontextmanager
from fastapi import FastAPI
from database.mongodb import mongodb

@asynccontextmanager
async def lifespan(app: FastAPI):
    await mongodb.connect()
    try:
        yield
    finally:
        await mongodb.disconnect()

app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(partner_controller.router, prefix="/api/v1", tags=["partners"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Hello, From IT KMITL."}
