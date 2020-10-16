
import time
import os
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
import httpx

# Set all environment variables
from app.setup import *

app = FastAPI()

motor_client = AsyncIOMotorClient(MONGO_DB_CONNECTION_STRING)
database = motor_client[ENVIRONMENT]
repo_collection = database['repositories']

httpx_client = httpx.AsyncClient(
    base_url="https://api.github.com",
    http2=True,
)

from app.routes import *  # nopep8
