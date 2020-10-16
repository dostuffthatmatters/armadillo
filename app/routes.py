
from fastapi import HTTPException, status
from app import app, httpx_client, ENVIRONMENT


@app.get('/')
def index_route():
    return {
        "status": "running",
        "mode": ENVIRONMENT
    }


@app.get('/{username}/{repository}')
async def get_commits(username, repository):
    response = await httpx_client.get(f"/repos/{username}/{repository}/commits")
    if response.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no repository @ 'github.com/{username}/{repository}'",
        )
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error",
        )

    return {
        "username": username,
        "repository": repository,
        "response": response.content,
        "status_code": response.status_code
    }
