
import time
import os
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

# Set all environment variables
from app.setup import *

app = FastAPI()

motor_client = AsyncIOMotorClient(MONGO_DB_CONNECTION_STRING)
database = motor_client[ENVIRONMENT]
repo_collection = database['repositories']
