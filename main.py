from controllers import auth_controller, user_controller, oauth_controller
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from database.mongodb import mongodb
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    await mongodb.connect()
    try:
        yield
    finally:
        await mongodb.disconnect()

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3031",
    "https://carb-partner.proserver.io:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # อนุญาตทุก Method (GET, POST, OPTIONS, etc.)
    allow_headers=["*"], # อนุญาตทุก Header
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    errors = [{"field": err["loc"][-1], "msg": err["msg"]} for err in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={"status": "fail", "errors": errors},
    )

# Include routers
app.include_router(auth_controller.router, prefix="/api/v1", tags=["auth"])
app.include_router(oauth_controller.router, prefix="/api/v1", tags=["oauth"])
app.include_router(user_controller.router, prefix="/api/v1", tags=["users"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Hello, From IT KMITL."}
