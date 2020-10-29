
import httpx
import os
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

ENVIRONMENT = os.getenv('ENVIRONMENT')
MONGO_DB_CONNECTION_STRING = os.getenv('MONGO_DB_CONNECTION_STRING')
IBM_API_KEY = os.getenv('IBM_API_KEY')
IBM_ACCESS_TOKEN = os.getenv('IBM_ACCESS_TOKEN')

app = FastAPI()

motor_client = AsyncIOMotorClient(MONGO_DB_CONNECTION_STRING)
database = motor_client[ENVIRONMENT]
repo_collection = database['repositories']

github_api_client = httpx.AsyncClient(
    base_url="https://api.github.com",
)

github_download_client = httpx.AsyncClient(
    base_url="https://github.com",
)

ibm_token_client = httpx.AsyncClient(
    base_url="https://iam.cloud.ibm.com/oidc",
    headers={
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
)

# File upload is not asyncronous
ibm_upload_client = httpx.Client(
    base_url="https://s3.eu-de.cloud-object-storage.appdomain.cloud/armadillo-repositories",
)

from app.routes import *  # nopep8
