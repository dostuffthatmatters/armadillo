
from dotenv import load_dotenv
import certifi
import os

# Set correct SSL certificate
os.environ['SSL_CERT_FILE'] = certifi.where()

# Initialize environment variables
ENVIRONMENT = os.getenv('ENVIRONMENT')
assert(ENVIRONMENT in [None, "testing"])

load_dotenv()

assert(all([
    isinstance(os.getenv(env_var), str) for env_var in [
        'ENVIRONMENT',
        'MONGO_DB_CONNECTION_STRING'
    ]
]))
assert(os.getenv('ENVIRONMENT') in ['production', 'development', 'testing'])

# Set environment if 'testing' has not already been set
ENVIRONMENT = os.getenv('ENVIRONMENT') if ENVIRONMENT is None else ENVIRONMENT

MONGO_DB_CONNECTION_STRING = os.getenv('MONGO_DB_CONNECTION_STRING')
