import requests


def create_test_listener(name: str):
    resp = requests.post(
        "http://localhost:9999/api/login",
        data={"username": "admin", "password": "admin"},
    )
    token = resp.json()["access_token"]
    session = requests.Session()
    session.headers = {"Authorization": f"Bearer {token}"}
    resp = session.get("http://localhost:9999/api/listener-templates/all")
    data = resp.json()
    set_options = {
        opt_name: opt["default_value"] for opt_name, opt in data[0]["options"].items()
    }
    set_options["name"] = name
    resp = session.post(
        f"http://localhost:9999/api/listener-templates/{data[0]["listener_template_id"]}",
        json=set_options,
    )
    data = resp.json()
    resp = session.post(
        f"http://localhost:9999/api/listeners/{data["listener_id"]}/start",
    )
    print(resp.json())


create_test_listener(name="Honoka")
