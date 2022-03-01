"""
System tests for the user routes in server.py.
H11A-quadruples, April 2020.
"""

import requests
from requests.exceptions import HTTPError
import pytest
from helpers.registers_http import user1, user2, chan1
from port_settings import PORT, BASE_URL

####################################################################
##                      Testing user/profile                      ##
####################################################################

def test_user_profile_valid():
    """
    A test for the user/profile route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    user1_id, user1_token = user1(PORT)
    user2_id, user2_token = user2(PORT)

    ## Call user/profile for user1 and assert the output is correct
    response = requests.get(f"{BASE_URL}/user/profile", params={
        "token": user1_token,
        "u_id": user1_id
    }).json()
    assert response == {
        "user": {
            "u_id": user1_id,
            "email": "bob.ross@unsw.edu.au",
            "name_first": "Bob",
            "name_last": "Ross",
            "handle_str": "bobross",
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        }
    }

    ## Call user/profile for user2 and assert the output is correct
    response = requests.get(f"{BASE_URL}/user/profile", params={
        "token": user2_token,
        "u_id": user2_id
    }).json()
    assert response == {
        "user": {
            "u_id": user2_id,
            "email": "elon.musk@unsw.edu.au",
            "name_first": "Elon",
            "name_last": "Musk",
            "handle_str": "elonmusk",
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        }
    }

def test_user_profile_invalid():
    """
    A test for the user/profile route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    user1_id, user1_token = user1(PORT)

    ## Attempt to call user/profile for an invalid u_id
    with pytest.raises(HTTPError):
        requests.get(f"{BASE_URL}/user/profile", params={
            "token": user1_token,
            "u_id": 999999 ## invalid id
        }).raise_for_status()

    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.get(f"{BASE_URL}/user/profile", params={
            "token": "11111",
            "u_id": user1_id
        }).raise_for_status()


####################################################################
##                  Testing user/profile/setname                  ##
####################################################################

def test_user_profile_setname_valid():
    """
    A test for the user/profile/setname route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    user1_id, user1_token = user1(PORT)

    ## user1 creates a channel
    ch1 = chan1(PORT, user1_token)

    ## Set user1's name
    requests.put(f"{BASE_URL}/user/profile/setname", json={
        "token": user1_token,
        "name_first": "Ross",
        "name_last": "Bob"
    })

    ## Check that user1's name is updated in their user/profile
    response = requests.get(f"{BASE_URL}/user/profile", params={
        "token": user1_token,
        "u_id": user1_id
    }).json()
    assert response == {
        "user": {
            "u_id": user1_id,
            "email": "bob.ross@unsw.edu.au",
            "name_first": "Ross",
            "name_last": "Bob",
            "handle_str": "bobross",
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"

        }
    }

    ## Check that user1's name is updated in their channel/details
    response = requests.get(f"{BASE_URL}/channel/details", params={
        "token": user1_token,
        "channel_id": ch1
    }).json()
    assert response["owner_members"] == [
        {
            "u_id": user1_id,
            "name_first": "Ross",
            "name_last": "Bob",
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        }
    ]
    assert response["all_members"] == [
        {
            "u_id": user1_id,
            "name_first": "Ross",
            "name_last": "Bob",
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        }
    ]

def test_user_profile_setname_invalid():
    """
    A test for the user/profile/setname route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    _, user1_token = user1(PORT)

    short_name = ""
    long_name = "a" * 51

    ## Attempt to set names to short names
    with pytest.raises(HTTPError):
        requests.put(f"{BASE_URL}/user/profile/setname", json={
            "token": user1_token,
            "name_first": short_name,
            "name_last": "harambe"
        }).raise_for_status()
    with pytest.raises(HTTPError):
        requests.put(f"{BASE_URL}/user/profile/setname", json={
            "token": user1_token,
            "name_first": "harambe",
            "name_last": short_name
        }).raise_for_status()

    ## Attempt to set names to long names
    with pytest.raises(HTTPError):
        requests.put(f"{BASE_URL}/user/profile/setname", json={
            "token": user1_token,
            "name_first": long_name,
            "name_last": "harambe"
        }).raise_for_status()
    with pytest.raises(HTTPError):
        requests.put(f"{BASE_URL}/user/profile/setname", json={
            "token": user1_token,
            "name_first": "harambe",
            "name_last": long_name
        }).raise_for_status()

    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.put(f"{BASE_URL}/user/profile/setname", json={
            "token": "11111",
            "name_first": "harambe",
            "name_last": "harambe"
        }).raise_for_status()


####################################################################
##                 Testing user/profile/setemail                  ##
####################################################################

def test_user_profile_setemail_valid():
    """
    A test for the user/profile/setemail route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    user1_id, user1_token = user1(PORT)

    ## user1 sets their email
    requests.put(f"{BASE_URL}/user/profile/setemail", json={
        "token": user1_token,
        "email": "bob.ross@gmail.com"
    })

    ## Check that user1's email is now updated
    response = requests.get(f"{BASE_URL}/user/profile", params={
        "token": user1_token,
        "u_id": user1_id
    }).json()
    assert response == {
        "user": {
            "u_id": user1_id,
            "email": "bob.ross@gmail.com",
            "name_first": "Bob",
            "name_last": "Ross",
            "handle_str": "bobross",
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        }
    }

def test_user_profile_setemail_invalid():
    """
    A test for the user/profile/setemail route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    _, user1_token = user1(PORT)
    user2(PORT)

    ## Attempt to set email to emails with invalid format
    with pytest.raises(HTTPError):
        requests.put(f"{BASE_URL}/user/profile/setemail", json={
            "token": user1_token,
            "email": "abc"
        }).raise_for_status()
    with pytest.raises(HTTPError):
        requests.put(f"{BASE_URL}/user/profile/setemail", json={
            "token": user1_token,
            "email": "@gmail.com"
        }).raise_for_status()

    ## Attempt to set user1's email to user2's email
    with pytest.raises(HTTPError):
        requests.put(f"{BASE_URL}/user/profile/setemail", json={
            "token": user1_token,
            "email": "elon.musk@unsw.edu.au"
        }).raise_for_status()

    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.put(f"{BASE_URL}/user/profile/setemail", json={
            "token": "11111",
            "email": "hi@gmail.com"
        }).raise_for_status()


####################################################################
##                Testing user/profile/sethandle                  ##
####################################################################

def test_user_profile_sethandle_valid():
    """
    A test for the user/profile/sethandle route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    user1_id, user1_token = user1(PORT)

    ## user1 sets their handle
    requests.put(f"{BASE_URL}/user/profile/sethandle", json={
        "token": user1_token,
        "handle_str": "bobrossisalive"
    })

    ## Check that their handle is updated
    response = requests.get(f"{BASE_URL}/user/profile", params={
        "token": user1_token,
        "u_id": user1_id
    }).json()
    assert response == {
        "user": {
            "u_id": user1_id,
            "email": "bob.ross@unsw.edu.au",
            "name_first": "Bob",
            "name_last": "Ross",
            "handle_str": "bobrossisalive",
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        }
    }

def test_user_profile_sethandle_invalid():
    """
    A test for the user/profile/sethandle route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    _, user1_token = user1(PORT)
    _, user2_token = user2(PORT)

    ## Attempt to set handle to a handle under 2 characters
    with pytest.raises(HTTPError):
        requests.put(f"{BASE_URL}/user/profile/sethandle", json={
            "token": user1_token,
            "handle_str": ""
        }).raise_for_status()
    with pytest.raises(HTTPError):
        requests.put(f"{BASE_URL}/user/profile/sethandle", json={
            "token": user1_token,
            "handle_str": "a"
        }).raise_for_status()

    ## Attempt to set handle to a handle over 20 characters
    with pytest.raises(HTTPError):
        requests.put(f"{BASE_URL}/user/profile/sethandle", json={
            "token": user1_token,
            "handle_str": "a" * 21
        }).raise_for_status()
    with pytest.raises(HTTPError):
        requests.put(f"{BASE_URL}/user/profile/sethandle", json={
            "token": user1_token,
            "handle_str": "a" * 1000
        }).raise_for_status()

    ## Attempt to set handle to a handle in use
    with pytest.raises(HTTPError):
        requests.put(f"{BASE_URL}/user/profile/sethandle", json={
            "token": user1_token,
            "handle_str": "elonmusk" ## taken by user2
        }).raise_for_status()
    with pytest.raises(HTTPError):
        requests.put(f"{BASE_URL}/user/profile/sethandle", json={
            "token": user2_token,
            "handle_str": "bobross" ## taken by user1
        }).raise_for_status()

    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.put(f"{BASE_URL}/user/profile/sethandle", json={
            "token": "11111",
            "handle_str": "bobby"
        }).raise_for_status()
