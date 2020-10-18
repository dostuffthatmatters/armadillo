
import json
from os import mkdir

import httpx
from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse

from app import (ENVIRONMENT, app, fetch_new_token, github_api_client,
                 github_download_client, repo_collection, storage_client)
import os


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

    response = await github_api_client.get(
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

    url = f'/{username}/{repository}/{file_path}'
    response_dict = json.loads(response.content)
    current_sha = response_dict[0]["sha"]
    db_document = await repo_collection.find_one(
        {"url": url},
        {"_id": 0, "sha": 1}
    )

    # update_zip = (db_document is None) or (db_document["sha"] != current_sha)
    update_zip = True

    if update_zip:

        print("updating zip")
        # TODO: renew stored file to be downloaded

        encoded_file_path = file_path.replace('/', '-')
        filename = f"{repository}-{encoded_file_path}"
        if username not in os.listdir("tmp"):
            os.mkdir(f"tmp/{username}")
        if repository not in os.listdir(f"tmp/{username}"):
            os.mkdir(f"tmp/{username}/{repository}")
        if filename not in os.listdir((f"tmp/{username}/{repository}")):
            os.mkdir(f"tmp/{username}/{repository}/{filename}")

        with open(f"tmp/{username}/{repository}/{filename}/master.zip", "wb") as file:
            response = await github_download_client.get(
                f"/{username}/{repository}/archive/master.zip"
            )
            file.write(response.content)

        await repo_collection.update_one(
            {"url": url}, {"$set": {"sha": current_sha}}, upsert=True
        )

    # TODO: Return file as download

    return {
        "username": username,
        "repository": repository,
        "status_code": response.status_code
    }


@app.get('/{username}/{repository}')
def download_root(username, repository):
    return RedirectResponse(
        f"https://github.com/{username}/{repository}" +
        "/archive/master.zip"
    )
