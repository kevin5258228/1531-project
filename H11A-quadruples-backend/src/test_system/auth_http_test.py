"""
System tests for the auth routes in server.py.
H11A-quadruples, April 2020.
"""

import requests
from requests.exceptions import HTTPError
import pytest
from helpers.registers_http import user1, user2
from port_settings import PORT, BASE_URL

####################################################################
##                      Testing auth/login                        ##
####################################################################

def test_auth_login_valid():
    """
    A test for the auth/login route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register two users
    user1_id, _ = user1(PORT)
    user2_id, _ = user2(PORT)

    ## Assert that the u_id returned from auth/login matches the above id"s
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "bob.ross@unsw.edu.au",
        "password": "pword123",
    }).json()
    u_id1 = response["u_id"]

    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "elon.musk@unsw.edu.au",
        "password": "pword456",
    }).json()
    u_id2 = response["u_id"]

    assert u_id1 == user1_id
    assert u_id2 == user2_id

def test_auth_login_invalid():
    """
    A test for the auth/login route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register a user with email bob.ross@unsw.edu.au
    user1(PORT)

    ## Attempt to log in with an invalidly formatted email
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/auth/login", json={
            "email": "unsw.edu.au",
            "password": "pword123",
        }).raise_for_status()

    ## Attempt to log in with a validly formatted but unregistered email
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/auth/login", json={
            "email": "james@unsw.edu.au",
            "password": "pword123",
        }).raise_for_status()

    ## Attempt to log in with an incorrect password for a registered account
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/auth/login", json={
            "email": "bob.ross@unsw.edu.au",
            "password": "pword999",
        }).raise_for_status()


####################################################################
##                     Testing auth/logout                        ##
####################################################################

def test_auth_logout_valid():
    """
    A test for the auth/logout route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register two users
    _, user1_token = user1(PORT)
    _, user2_token = user2(PORT)

    ## Posting request to log out with the token
    response1 = requests.post(f"{BASE_URL}/auth/logout", json={
        "token": user1_token
    }).json()
    response2 = requests.post(f"{BASE_URL}/auth/logout", json={
        "token": user2_token
    }).json()

    ## Checking response is true
    assert response1 == {"is_success": True}
    assert response2 == {"is_success": True}

def test_auth_logout_invalid():
    """
    A test for the auth/logout route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/auth/logout", json={
            "token": "11111"
        }).raise_for_status()


####################################################################
##                    Testing auth/register                       ##
####################################################################

def test_auth_register_valid():
    """
    A test for the auth/register route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register a user
    response1 = requests.post(f"{BASE_URL}/auth/register", json={
        "email": "bob.ross@unsw.edu.au",
        "password": "pword123",
        "name_first": "Bob",
        "name_last": "Ross"
    }).json()

    ## Assert that the user exists
    users = requests.get(f"{BASE_URL}/users/all", params={
        "token": response1["token"]
    }).json()
    assert users == {
        "users": [
            {
                "u_id": response1["u_id"],
                "email": "bob.ross@unsw.edu.au",
                "name_first": "Bob",
                "name_last": "Ross",
                "handle_str": "bobross",
                "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
            }
        ]
    }

    ## Register a user with the same name_first and name_last
    response2 = requests.post(f"{BASE_URL}/auth/register", json={
        "email": "other.bob@unsw.edu.au",
        "password": "pword123",
        "name_first": "Bob",
        "name_last": "Ross"
    }).json()

    ## Assert the user was registered and his handle is unique
    users = requests.get(f"{BASE_URL}/users/all", params={
        "token": response2["token"]
    }).json()
    assert users == {
        "users": [
            {
                "u_id": response1["u_id"],
                "email": "bob.ross@unsw.edu.au",
                "name_first": "Bob",
                "name_last": "Ross",
                "handle_str": "bobross",
                "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
            },
            {
                "u_id": response2["u_id"],
                "email": "other.bob@unsw.edu.au",
                "name_first": "Bob",
                "name_last": "Ross",
                "handle_str": "bobross1", ## unique handle
                "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
            }
        ]
    }

def test_auth_register_invalid():
    """
    A test for the auth/register route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    ## Attempt to register with an invalidly formatted email
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/auth/register", json={
            "email": "unsw.edu.au",
            "password": "pword123",
            "name_first": "Bob",
            "name_last": "Smith"
        }).raise_for_status()

    ## Register a user with email bob.ross@unsw.edu.au and attempt to
    ## register another user with the same email
    user1(PORT)
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/auth/register", json={
            "email": "bob.ross@unsw.edu.au",
            "password": "pword000",
            "name_first": "Bob",
            "name_last": "Smith"
        }).raise_for_status()

    ## Attempt to register with a weak password
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/auth/register", json={
            "email": "james@unsw.edu.au",
            "password": "yes",
            "name_first": "Bob",
            "name_last": "Smith"
        }).raise_for_status()

    ## Attempt to register with an invalid name_first
    short_name = ""
    long_name = "a" * 51
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/auth/register", json={
            "email": "james@unsw.edu.au",
            "password": "pword000",
            "name_first": short_name,
            "name_last": "Smith"
        }).raise_for_status()
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/auth/register", json={
            "email": "james@unsw.edu.au",
            "password": "pword000",
            "name_first": long_name,
            "name_last": "Smith"
        }).raise_for_status()

    ## Attempt to register with an invalid name_last
    short_name = ""
    long_name = "a" * 51
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/auth/register", json={
            "email": "james@unsw.edu.au",
            "password": "pword000",
            "name_first": "Bob",
            "name_last": short_name
        }).raise_for_status()
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/auth/register", json={
            "email": "james@unsw.edu.au",
            "password": "pword000",
            "name_first": "Bob",
            "name_last": long_name
        }).raise_for_status()
