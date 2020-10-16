
from app import app, httpx_client, ENVIRONMENT


@app.get('/')
def index_route():
    return {
        "status": "running",
        "mode": ENVIRONMENT
    }


@app.get('/{username}/{repository}')
async def get_commits(username, repository):
    response = await httpx_client.get("/repos/{username}/{repository}/commits")
    return {
        "username": username,
        "repository": repository,
        "response": response.content
    }
