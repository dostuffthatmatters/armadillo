
from dotenv import load_dotenv
import certifi
import os
import httpx
import json

# Set correct SSL certificate
os.environ['SSL_CERT_FILE'] = certifi.where()

# Initialize environment variables
ENVIRONMENT = os.getenv('ENVIRONMENT')
assert(ENVIRONMENT in [None, "testing"])

load_dotenv()

assert(all([
    isinstance(os.getenv(env_var), str) for env_var in [
        'ENVIRONMENT',
        'MONGO_DB_CONNECTION_STRING',
        'IBM_API_KEY'
    ]
]))
assert(os.getenv('ENVIRONMENT') in ['production', 'development', 'testing'])

# Set environment if 'testing' has not already been set
ENVIRONMENT = os.getenv('ENVIRONMENT') if ENVIRONMENT is None else ENVIRONMENT

MONGO_DB_CONNECTION_STRING = os.getenv('MONGO_DB_CONNECTION_STRING')
IBM_API_KEY = os.getenv('IBM_API_KEY')

token_client = httpx.Client(
    base_url="https://iam.cloud.ibm.com/oidc",
    headers={
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    }
)

response = token_client.post("/token", data={
    "apikey": IBM_API_KEY,
    "response_type": "cloud_iam",
    "grant_type": "urn:ibm:params:oauth:grant-type:apikey"
})
assert(response.status_code == 200)
obj = json.loads(response.content.decode())
assert("access_token" in obj)
IBM_ACCESS_TOKEN = obj["access_token"]
