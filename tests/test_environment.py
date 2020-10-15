import json
from tests.conftest import get_content_dict


def test_environment(client):
    # Test whether backend is running in correct mode
    response = client.get("/")
    assert(response.status_code == 200)
    content_dict = get_content_dict(response)
    assert(all([key in content_dict for key in ["status", "mode"]]))
    assert(content_dict["mode"] == "testing")
