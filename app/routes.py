
import json
from os import mkdir
import shutil
from zipfile import ZipFile

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
            detail=f"nothing found @ '/{username}/{repository}/{file_path}'",
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

        default_branch = await get_default_branch(username, repository)

        encoded_file_path = file_path.replace('/', '-')
        filename = f"{repository}-{encoded_file_path}"
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

        shutil.rmtree(f"{tmp_dir}")
        if len(os.listdir(f"tmp/{username}/{repository}")) == 0:
            shutil.rmtree(f"tmp/{username}")

        # TODO: Upload file to IBM Object Storage

        await repo_collection.update_one(
            {"url": url}, {"$set": {"sha": current_sha}}, upsert=True
        )

    # TODO: Return file as download link

    return {
        "username": username,
        "repository": repository,
        "status_code": response.status_code
    }


@app.get('/{username}/{repository}')
async def download_root(username, repository):

    default_branch = await get_default_branch(username, repository)

    return RedirectResponse(
        f"https://github.com/{username}/{repository}" +
        f"/archive/{default_branch}.zip"
    )


async def get_default_branch(username, repository):
    response = await github_api_client.get(
        f"/repos/{username}/{repository}"
    )
    if response.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"nothing found @ '/{username}/{repository}'",
        )
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error",
        )

    return json.loads(response.content)["default_branch"]
