
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


# Unused (nopep8)
async def is_valid_path(username, repository, default_branch, file_path):
    response = await github_download_client.get(
        f"/{username}/{repository}/tree/{default_branch}/{file_path}"
    )
    return response.status_code == 200


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

    # 1. Create working directory for re-zipping
    #    repo name already included in filename
    tmp_dir = f"tmp/{username}/{filename}"
    if username not in os.listdir("tmp"):
        os.mkdir(f"tmp/{username}")
    if filename not in os.listdir((f"tmp/{username}")):
        os.mkdir(tmp_dir)

    # 2. Download the whole repo-zip
    with open(f"{tmp_dir}/{default_branch}.zip", "wb") as file:
        response = await github_download_client.get(
            f"/{username}/{repository}/archive/{default_branch}.zip"
        )
        file.write(response.content)

    with ZipFile(f"{tmp_dir}/{default_branch}.zip", 'r') as zip:
        # 3. Check the validity of the repo-zip
        if f"{repository}-{default_branch}/" not in zip.namelist():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"GitHub API did not respond as expected",
            )

        # 4. Check if the path actually exists. Edge case:
        #    file_path did exist at some point but does not exist
        #    anymore AND the zip has not yet been generated
        if f"{repository}-{default_branch}/{file_path}" not in zip.namelist():
            # I could have put this captcha at position 1 to avoid
            # useless zip-downloads, but this edge case is so rare
            # that by moving it here I will save one extra request
            # on nearly all requests with rezipping
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"subdirectory used to exist but not anymore",
            )
        # 5. Unzip it
        zip.extractall(tmp_dir)

    # 6. 'Rezip' the contents = Generate the subdirectory-zip
    with ZipFile(f"{tmp_dir}/{filename}.zip", 'w') as zip:

        path_list = file_path.split('/')
        parent_path = "./" + "/".join(path_list[:-1])
        subdir_name = path_list[-1]

        # Switch into the folder where the subdirectory
        # to be zipped is located (the parent of the file-path)
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

    # 7. Upload file to IBM object storage (not asyncronous)
    response = ibm_upload_client.put(
        f"/{username}/{filename}.zip",
        data=open(f"{tmp_dir}/{filename}.zip", 'rb'),
        headers={"Authorization": "bearer " + os.getenv("IBM_ACCESS_TOKEN")}
    )

    # 8. If that upload did not work (IBM OAuth token expired)
    #    The storage tokens expire ever 3600 seconds (1 hour)
    if response.status_code == 401:
        await generate_new_storage_token()
        # (9.) Upload again with new token
        response = ibm_upload_client.put(
            f"/{username}/{filename}.zip",
            data=open(f"{tmp_dir}/{filename}.zip", 'rb'),
            headers={"Authorization": "bearer " + os.getenv("IBM_ACCESS_TOKEN")}
        )

    # 10. Raise error if upload still did not work
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"IBM Storage API did not respond as expected",
        )

    # 11. Remove working directory of this Rezipping
    shutil.rmtree(f"{tmp_dir}")

    # 12. Remove that users tmp dir (when no other
    #     rezipping is happening concurrently)
    if len(os.listdir(f"tmp/{username}")) == 0:
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
