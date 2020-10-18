
import json
from os import mkdir
import shutil
from zipfile import ZipFile

import httpx
from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse

from app import (ENVIRONMENT, app, fetch_new_token, github_api_client,
                 github_download_client, repo_collection, storage_client)
from app.utilities import get_default_branch, get_current_sha, generate_subdir_zip
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

    url = f'/{username}/{repository}/{file_path}'
    current_sha = await get_current_sha(username, repository, file_path)
    db_document = await repo_collection.find_one(
        {"url": url},
        {"_id": 0, "sha": 1}
    )

    encoded_file_path = file_path.replace('/', '-')
    filename = f"{repository}-{encoded_file_path}"

    if (db_document is None) or (db_document["sha"] != current_sha):
        await generate_subdir_zip(username, repository, file_path, filename)
        await repo_collection.update_one(
            {"url": url}, {"$set": {"sha": current_sha}}, upsert=True
        )

    return RedirectResponse(
        "https://s3.eu-de.cloud-object-storage.appdomain.cloud/armadillo-repositories" +
        f"/{username}/{repository}/{filename}.zip"
    )


@app.get('/{username}/{repository}')
async def download_root(username, repository):

    default_branch = await get_default_branch(username, repository)

    return RedirectResponse(
        f"https://github.com/{username}/{repository}" +
        f"/archive/{default_branch}.zip"
    )
