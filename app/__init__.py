
import httpx
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

# Set all environment variables
from app.setup import *

app = FastAPI()

motor_client = AsyncIOMotorClient(MONGO_DB_CONNECTION_STRING)
database = motor_client[ENVIRONMENT]
repo_collection = database['repositories']

github_api_client = httpx.AsyncClient(
    base_url="https://api.github.com",
    http2=True,
)

github_download_client = httpx.AsyncClient(
    base_url="https://github.com",
    http2=True,
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
    headers={"Authorization": f"bearer {IBM_ACCESS_TOKEN}"}
)

from app.routes import *  # nopep8
