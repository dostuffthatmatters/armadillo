
from app import app, ENVIRONMENT


@app.get('/')
def index_route():
    return {
        "status": "running",
        "mode": ENVIRONMENT
    }
