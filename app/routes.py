
import json
from os import mkdir
import shutil
from zipfile import ZipFile

import httpx
from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse

from app import (ENVIRONMENT, app, fetch_new_token, github_api_client,
                 github_download_client, repo_collection, storage_client)
from app.utilities import get_default_branch, get_current_sha
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

        default_branch = await get_default_branch(username, repository)
        tmp_dir = f"tmp/{username}/{repository}/{filename}"
        if username not in os.listdir("tmp"):
            os.mkdir(f"tmp/{username}")
        if repository not in os.listdir(f"tmp/{username}"):
            os.mkdir(f"tmp/{username}/{repository}")
        if filename not in os.listdir((f"tmp/{username}/{repository}")):
            os.mkdir(tmp_dir)

        with open(f"{tmp_dir}/{default_branch}.zip", "wb") as file:
            response = await github_download_client.get(
                f"/{username}/{repository}/archive/{default_branch}.zip"
            )
            file.write(response.content)

        with ZipFile(f"{tmp_dir}/{default_branch}.zip", 'r') as zip:
            if f"{repository}-{default_branch}/" not in zip.namelist():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"GitHub API did not respond as expected",
                )
            zip.extractall(tmp_dir)

        # writing files to a zipfile
        with ZipFile(f"{tmp_dir}/{filename}.zip", 'w') as zip:
            os.chdir(f"{tmp_dir}/{repository}-{default_branch}/{file_path}/..")
            folder_name = file_path.split('/')[-1]
            file_list = os.listdir(folder_name)
            for file in file_list:
                zip.write(f"{folder_name}/{file}")
            os.chdir("../" * (4 + len(file_path.split('/'))))

        response = storage_client.put(
            f"/{username}/{repository}/{filename}.zip",
            data=open(f"{tmp_dir}/{filename}.zip", 'rb')
        )
        if response.status != 200:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"IBM Storage API did not respond as expected",
            )

        shutil.rmtree(f"{tmp_dir}")
        if len(os.listdir(f"tmp/{username}/{repository}")) == 0:
            shutil.rmtree(f"tmp/{username}")

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
