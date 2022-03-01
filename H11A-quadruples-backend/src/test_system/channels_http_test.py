"""
System tests for the channels routes in server.py.
H11A-quadruples, April 2020.
"""

import requests
from requests.exceptions import HTTPError
import pytest
from helpers.registers_http import user1, user2, chan1, chan2, chan3, join_req
from port_settings import PORT, BASE_URL

####################################################################
##                    Testing channels/list                       ##
####################################################################

def test_channels_list_two_users():
    """
    A test for the channels/list route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register 2 users
    _, user1_token = user1(PORT)
    _, user2_token = user2(PORT)

    ## user1 creates 2 channels
    ch1 = chan1(PORT, user1_token)
    ch2 = chan2(PORT, user1_token)

    ## user2 creates 1 channel
    ch3 = chan3(PORT, user2_token)

    ## Request user1"s channel list
    response = requests.get(f"{BASE_URL}/channels/list", params={
        "token": user1_token
    }).json()

    ## Assert the response is correct
    assert response == {
        "channels": [
            {
                "channel_id": ch1,
                "name": "channel1"
            },
            {
                "channel_id": ch2,
                "name": "channel2"
            }
        ]
    }

    ## Assert user2"s channel list is correct
    response = requests.get(f"{BASE_URL}/channels/list", params={
        "token": user2_token
    }).json()

    ## Assert the response is correct
    assert response == {
        "channels": [
            {
                "channel_id": ch3,
                "name": "channel3"
            }
        ]
    }

def test_channels_list_join():
    """
    A test for the channels/list route under valid input (when a user
    joins a channel their channels list should be updated).
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register 2 users
    _, user1_token = user1(PORT)
    _, user2_token = user2(PORT)

    ## user1 creates a channel
    ch1 = chan1(PORT, user1_token)

    ## user2 creates a channel
    ch2 = chan2(PORT, user2_token)

    ## Check user2's channels before joining
    response = requests.get(f"{BASE_URL}/channels/list", params={
        "token": user2_token
    }).json()
    assert response == {
        "channels": [
            {
                "channel_id": ch2,
                "name": "channel2"
            }
        ]
    }

    ## user2 joins channel1
    join_req(PORT, user2_token, ch1)

    ## Check user2's channels after joining
    response = requests.get(f"{BASE_URL}/channels/list", params={
        "token": user2_token
    }).json()
    assert response == {
        "channels": [
            {
                "channel_id": ch1,
                "name": "channel1"
            },
            {
                "channel_id": ch2,
                "name": "channel2"
            }
        ]
    }

def test_channels_list_leave():
    """
    A test for the channels/list route under valid input (when a user
    leaves a channel their channels list should be updated).
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register a user
    _, user1_token = user1(PORT)

    ## user1 creates 2 channels
    ch1 = chan1(PORT, user1_token)
    ch2 = chan2(PORT, user1_token)

    ## Check user1"s channels before leaving
    response = requests.get(f"{BASE_URL}/channels/list", params={
        "token": user1_token
    }).json()
    assert response == {
        "channels": [
            {
                "channel_id": ch1,
                "name": "channel1"
            },
            {
                "channel_id": ch2,
                "name": "channel2"
            }
        ]
    }

    ## user1 leaves channel2
    requests.post(f"{BASE_URL}/channel/leave", json={
        "token": user1_token,
        "channel_id": ch2
    })

    ## Check user1"s channel list
    response = requests.get(f"{BASE_URL}/channels/list", params={
        "token": user1_token
    }).json()
    assert response == {
        "channels": [
            {
                "channel_id": ch1,
                "name": "channel1"
            }
        ]
    }

def test_channels_list_empty():
    """
    A test for the channels/list route under valid input (when a user
    has not joined any channels).
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register a user
    _, user1_token = user1(PORT)

    ## Check user1"s channel list
    response = requests.get(f"{BASE_URL}/channels/list", params={
        "token": user1_token
    }).json()
    assert response == {"channels": []}

def test_channels_list_invalid():
    """
    A test for the channels/list route under invalid input.
    """
    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.get(f"{BASE_URL}/channels/list", params={
            "token": "11111"
        }).raise_for_status()


####################################################################
##                   Testing channels/listall                     ##
####################################################################

def test_channels_listall_valid():
    """
    A test for the channels/listall route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register 2 users
    _, user1_token = user1(PORT)
    _, user2_token = user2(PORT)

    ## user1 creates 2 channels
    ch1 = chan1(PORT, user1_token)
    ch2 = chan2(PORT, user1_token)

    ## user2 creates 1 channel
    ch3 = chan3(PORT, user2_token)

    ## Check channels_listall output
    response1 = requests.get(f"{BASE_URL}/channels/listall", params={
        "token": user1_token
    }).json()
    assert response1 == {
        "channels": [
            {
                "channel_id": ch1,
                "name": "channel1"
            },
            {
                "channel_id": ch2,
                "name": "channel2"
            },
            {
                "channel_id": ch3,
                "name": "channel3"
            }
        ]
    }

    ## If user2 makes the request the output should be the same
    response2 = requests.get(f"{BASE_URL}/channels/listall", params={
        "token": user2_token
    }).json()
    assert response1 == response2

def test_channels_listall_empty():
    """
    A test for the channels/listall route under valid input (no channels).
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register a user
    _, user1_token = user1(PORT)

    ## Assert the list of channels is empty
    response = requests.get(f"{BASE_URL}/channels/listall", params={
        "token": user1_token
    }).json()
    assert response == {"channels": []}

def test_channels_listall_invalid():
    """
    A test for the channels/listall route under invalid input.
    """
    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.get(f"{BASE_URL}/channels/listall", params={
            "token": "11111"
        }).raise_for_status()


####################################################################
##                   Testing channels/create                      ##
####################################################################

def test_channels_create_valid():
    """
    A test for the channels/create route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register a user
    _, user1_token = user1(PORT)

    ## Assert that no channels are yet created
    response = requests.get(f"{BASE_URL}/channels/listall", params={
        "token": user1_token
    }).json()
    assert response == {"channels": []}

    ## user1 creates a public channel
    response = requests.post(f"{BASE_URL}/channels/create", json={
        "token": user1_token,
        "name": "channel1",
        "is_public": True,
    }).json()
    ch1 = response["channel_id"]

    ## Assert that the channel has been created
    response = requests.get(f"{BASE_URL}/channels/listall", params={
        "token": user1_token
    }).json()
    assert response == {
        "channels": [
            {
                "channel_id": ch1,
                "name": "channel1"
            }
        ]
    }

def test_channels_create_invalid():
    """
    A test for the channels/create route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register a user
    _, user1_token = user1(PORT)

    ## Attempt to create a channel with a long name
    long_name = "a" * 21
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/channels/create", json={
            "token": user1_token,
            "name": long_name,
            "is_public": True,
        }).raise_for_status()

    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/channels/create", json={
            "token": "11111",
            "name": "channel1",
            "is_public": True,
        }).raise_for_status()
