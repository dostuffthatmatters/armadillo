
import json
import os
import shutil
from os.path import isdir
from zipfile import ZipFile

from fastapi import HTTPException, status

from app.main import (IBM_API_KEY, github_api_client, github_download_client,
                      ibm_token_client, ibm_upload_client)


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


async def get_current_sha(username, repository, file_path):
    response = await github_api_client.get(
        f"/repos/{username}/{repository}/commits",
        params={"path": file_path}
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

    response_dict = json.loads(response.content)
    if len(response_dict) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"nothing found in subdirectory @ '/{username}/{repository}/{file_path}'",
        )

    return response_dict[0]["sha"]


async def generate_subdir_zip(username, repository, file_path, filename):
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
        path_list = file_path.split('/')
        parent_path = "./" + "/".join(path_list[:-1])
        subdir_name = path_list[-1]

        relative_working_directory = \
            f"{tmp_dir}/{repository}-{default_branch}/{parent_path}"
        os.chdir(relative_working_directory)

        # Object at path is a directory
        if os.path.isdir(subdir_name):
            file_list = os.listdir(subdir_name)
            for file in file_list:
                zip.write(f"{subdir_name}/{file}")

        # Object at path is single file
        else:
            zip.write(subdir_name)

        # Move back to initial directory
        os.chdir("../" * len(relative_working_directory))

    # File upload are not asyncronous
    response = ibm_upload_client.put(
        f"/{username}/{repository}/{filename}.zip",
        data=open(f"{tmp_dir}/{filename}.zip", 'rb'),
        headers={"Authorization": "bearer " + os.getenv("IBM_ACCESS_TOKEN")}
    )

    if response.status_code == 401:
        # The storage tokens expire ever 3600 seconds (1 hour)
        await generate_new_storage_token()
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"IBM Storage API did not respond as expected",
        )

    shutil.rmtree(f"{tmp_dir}")
    if len(os.listdir(f"tmp/{username}/{repository}")) == 0:
        shutil.rmtree(f"tmp/{username}")


async def generate_new_storage_token():
    response = await ibm_token_client.post("/token", data={
        "apikey": IBM_API_KEY,
        "response_type": "cloud_iam",
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey"
    })
    assert(response.status_code == 200)
    obj = json.loads(response.content.decode())
    assert("access_token" in obj)
    os.environ["IBM_ACCESS_TOKEN"] = obj["access_token"]
