
import time
import os
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
import httpx
import json

# Set all environment variables
from app.setup import *

app = FastAPI()

motor_client = AsyncIOMotorClient(MONGO_DB_CONNECTION_STRING)
database = motor_client[ENVIRONMENT]
repo_collection = database['repositories']

github_client = httpx.AsyncClient(
    base_url="https://api.github.com",
    http2=True,
)

token_client = httpx.AsyncClient(
    base_url="https://iam.cloud.ibm.com/oidc",
    headers={
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
)

storage_client = httpx.AsyncClient(
    base_url="https://storage.googleapis.com/storage/v1/b",
    http2=True,
    params={"key": IBM_ACCESS_TOKEN}
)


async def fetch_new_token():

    response = await token_client.post("/token", data={
        "apikey": IBM_API_KEY,
        "response_type": "cloud_iam",
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey"
    })
    assert(response.status_code == 200)
    obj = json.loads(response.content.decode())
    assert("access_token" in obj)
    IBM_ACCESS_TOKEN = obj["access_token"]

    storage_client.params = {"key": IBM_ACCESS_TOKEN}

from app.routes import *  # nopep8
