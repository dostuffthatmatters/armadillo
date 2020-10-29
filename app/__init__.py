
import certifi
import os
import httpx
import json

# Set correct SSL certificate
os.environ['SSL_CERT_FILE'] = certifi.where()

assert(os.getenv('ENVIRONMENT') in ['development', 'production'])
assert(os.getenv('MONGO_DB_CONNECTION_STRING') is not None)
assert(os.getenv('IBM_API_KEY') is not None)

token_response = httpx.post(
    "https://iam.cloud.ibm.com/oidc/token",
    headers={
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"
    },
    data={
        "apikey": os.getenv('IBM_API_KEY'),
        "response_type": "cloud_iam",
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey"
    }
)
assert(token_response.status_code == 200)
obj = json.loads(token_response.content.decode())
assert("access_token" in obj)
os.environ["IBM_ACCESS_TOKEN"] = obj["access_token"]

if "tmp" not in os.listdir("."):
    os.mkdir("tmp")
