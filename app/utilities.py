
import json
from fastapi import HTTPException, status
from app import github_api_client


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
