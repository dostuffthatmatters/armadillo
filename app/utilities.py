
import json
import os
import shutil
from zipfile import ZipFile

from fastapi import HTTPException, status

from app import github_api_client, github_download_client, \
    ibm_token_client, ibm_upload_client, IBM_API_KEY


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
        os.chdir(f"{tmp_dir}/{repository}-{default_branch}/{file_path}/..")
        folder_name = file_path.split('/')[-1]
        file_list = os.listdir(folder_name)
        for file in file_list:
            zip.write(f"{folder_name}/{file}")
        os.chdir("../" * (4 + len(file_path.split('/'))))

    # File upload are not asyncronous
    response = ibm_upload_client.put(
        f"/{username}/{repository}/{filename}.zip",
        data=open(f"{tmp_dir}/{filename}.zip", 'rb')
    )

    if response.status_code == 401:
        # The storage tokens expire ever 3600 seconds (1 hour)
        await generate_new_storage_token(ibm_upload_client)
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"IBM Storage API did not respond as expected",
        )

    shutil.rmtree(f"{tmp_dir}")
    if len(os.listdir(f"tmp/{username}/{repository}")) == 0:
        shutil.rmtree(f"tmp/{username}")


async def generate_new_storage_token(client_with_authentication):
    response = await ibm_token_client.post("/token", data={
        "apikey": IBM_API_KEY,
        "response_type": "cloud_iam",
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey"
    })
    assert(response.status_code == 200)
    obj = json.loads(response.content.decode())
    assert("access_token" in obj)
    IBM_ACCESS_TOKEN = obj["access_token"]

    client_with_authentication.headers = {
        "Authorization": f"bearer {IBM_ACCESS_TOKEN}"
    }
