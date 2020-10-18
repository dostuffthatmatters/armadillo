
from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse
from app import app, ENVIRONMENT, repo_collection, \
    github_client, storage_client, fetch_new_token
import json


@app.get('/')
def index_route():
    return {
        "status": "running",
        "mode": ENVIRONMENT
    }


@app.get('/{username}/{repository}/{file_path:path}')
async def download_subdirectory(username, repository, file_path: str):
    try:
        assert(len(file_path) > 0)
        assert(file_path[0] != "/")
    except AssertionError:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            details=f"invalid file_path '{file_path}'"
        )

    response = await github_client.get(
        f"/repos/{username}/{repository}/commits",
        params={"path": file_path}
    )
    if response.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"nothing found @ '/{username}/{repository}/{path}'",
        )
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error",
        )

    # return response.content

    url = f'/{username}/{repository}/{file_path}'
    response_dict = json.loads(response.content)
    current_sha = response_dict[0]["sha"]
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
        # open("tmp/{username}/{repository}")
        # TODO: renew stored file to be downloaded
        pass

    # TODO: Return file as download

    return {
        "username": username,
        "repository": repository,
        "response_dict": response_dict,
        "status_code": response.status_code
    }


@app.get('/{username}/{repository}')
def download_root(username, repository):
    return RedirectResponse(
        f"https://github.com/{username}/{repository}" +
        "/archive/master.zip"
    )
