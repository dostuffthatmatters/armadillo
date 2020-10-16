
from fastapi import HTTPException, status
from app import app, httpx_client, ENVIRONMENT, repo_collection


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

    url = f'/{username}/{repository}'
    current_sha = response.content["sha"]
    db_document = await repo_collection.find_one(
        {"url": url},
        {"_id": 0, "sha": 1}
    )

    update_zip = (db_document is None) or (db_document["sha"] != current_sha)
    if db_document is None:
        await repo_collection.insert_one(
            {"url": url, "sha": current_sha}
        )

    if update_zip:
        # TODO: renew stored file to be downloaded
        pass

    # TODO: Return file as download

    return {
        "username": username,
        "repository": repository,
        "response": response.content,
        "status_code": response.status_code
    }
