"""
System tests for the channel routes in server.py.
H11A-quadruples, April 2020.
"""

import requests
from requests.exceptions import HTTPError
import pytest
from helpers.registers_http import user1, user2, user3, chan1, join_req
from port_settings import PORT, BASE_URL

####################################################################
##                     Testing channel/invite                     ##
####################################################################

def test_channel_invite_valid():
    """
    A test for the channel/invite route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register user1 and user2
    user1_id, user1_token = user1(PORT)
    user2_id, user2_token = user2(PORT)

    ## user1 creates a channel
    ch1 = chan1(PORT, user1_token)

    ## Invite user2 to join channel1
    requests.post(f"{BASE_URL}/channel/invite", json={
        "token": user1_token,
        "channel_id": ch1,
        "u_id": user2_id
    })

    ## Assert that the user has joined
    response1 = requests.get(f"{BASE_URL}/channel/details", params={
        "token": user1_token,
        "channel_id": ch1
    }).json()
    assert response1["all_members"] == [
        {
            "u_id": user1_id,
            "name_first": "Bob",
            "name_last": "Ross",
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        },
        {
            "u_id": user2_id,
            "name_first": "Elon",
            "name_last": "Musk",
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        }
    ]

    ## Assert the response should be the same if user2 made the request
    response2 = requests.get(f"{BASE_URL}/channel/details", params={
        "token": user2_token,
        "channel_id": ch1
    }).json()
    assert response2 == response1

def test_channel_invite_invalid():
    """
    A test for the channel/invite route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    ## Register user1, user2 and user3
    _, user1_token = user1(PORT)
    user2_id, user2_token = user2(PORT)
    user3_id, _ = user3(PORT)

    ## user1 creates a channel
    ch1 = chan1(PORT, user1_token)

    ## User2 will attempt to invite a third user to user1's channel
    ## but user2 hasnt joined the channel yet
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/channel/invite", json={
            "token": user2_token,
            "channel_id": ch1,
            "u_id": user3_id
        }).raise_for_status()

    ## user1 attempts to invite a nonexistent user
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/channel/invite", json={
            "token": user1_token,
            "channel_id": ch1,
            "u_id": 99999 ## invalid id
        }).raise_for_status()

    ## Let user2 join channel1
    join_req(PORT, user2_token, ch1)

    ## user1 attempts to invite user2 but they are already in the channel
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/channel/invite", json={
            "token": user1_token,
            "channel_id": ch1,
            "u_id": user2_id
        }).raise_for_status()

    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/channel/invite", json={
            "token": "111111",
            "channel_id": ch1,
            "u_id": user3_id
        }).raise_for_status()


####################################################################
##                     Testing channel/details                    ##
####################################################################

def test_channel_details_valid():
    """
    A test for the channel/details route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register user1
    user1_id, user1_token = user1(PORT)

    ## user1 creates a channel
    ch1 = chan1(PORT, user1_token)

    ## Get the channel's details
    response = requests.get(f"{BASE_URL}/channel/details", params={
        "token": user1_token,
        "channel_id": ch1
    }).json()

    ## Assert the details are correct
    assert response["name"] == "channel1"
    assert response["owner_members"] == [
        {
            "u_id": user1_id,
            "name_first": "Bob",
            "name_last": "Ross",
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        }
    ]
    assert response["all_members"] == [
        {
            "u_id": user1_id,
            "name_first": "Bob",
            "name_last": "Ross",
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        }
    ]

def test_channel_details_invalid():
    """
    A test for the channel/details route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register user1 and user2
    _, user1_token = user1(PORT)
    _, user2_token = user2(PORT)

    ## Attempt to get a nonexistent channel's details
    with pytest.raises(HTTPError):
        requests.get(f"{BASE_URL}/channel/details", params={
            "token": user1_token,
            "channel_id": -9999
        }).raise_for_status()

    ## user1 creates a channel
    ch1 = chan1(PORT, user1_token)

    ## user2 attempts to get channel1's details when they aren't a member
    with pytest.raises(HTTPError):
        requests.get(f"{BASE_URL}/channel/details", params={
            "token": user2_token,
            "channel_id": ch1
        }).raise_for_status()

    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.get(f"{BASE_URL}/channel/details", params={
            "token": "11111",
            "channel_id": ch1
        }).raise_for_status()


####################################################################
##                    Testing channel/messages                    ##
####################################################################

def test_channel_messages_valid():
    """
    A test for the channel/messages route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register user1 and user2
    _, user1_token = user1(PORT)
    _, user2_token = user2(PORT)

    ## user1 creates a channel and user2 joins the channel
    ch1 = chan1(PORT, user1_token)
    join_req(PORT, user2_token, ch1)

    ## user1 and user2 send a message to channel1
    msg1 = requests.post(f"{BASE_URL}/message/send", json={
        "token": user1_token,
        "channel_id": ch1,
        "message": "user1's message"
    }).json()
    msg2 = requests.post(f"{BASE_URL}/message/send", json={
        "token": user2_token,
        "channel_id": ch1,
        "message": "user2's message"
    }).json()

    ## Call channel/messages
    chan_msgs = requests.get(f"{BASE_URL}/channel/messages", params={
        "token": user1_token,
        "channel_id": ch1,
        "start": 0
    }).json()

    ## Check start and end values are correct
    assert chan_msgs["start"] == 0
    assert chan_msgs["end"] == -1

    ## Check channel messages are correct
    assert chan_msgs["messages"][1]["message_id"] == msg1["message_id"]
    assert chan_msgs["messages"][0]["message_id"] == msg2["message_id"]

    ## Let user1 send 50 more messages to channel1
    for _ in range(50):
        requests.post(f"{BASE_URL}/message/send", json={
            "token": user1_token,
            "channel_id": ch1,
            "message": "user1's message"
        })

    ## Get channel/messages and assert end value is not -1
    chan_msgs = requests.get(f"{BASE_URL}/channel/messages", params={
        "token": user1_token,
        "channel_id": ch1,
        "start": 0
    }).json()

    assert chan_msgs["start"] == 0
    assert chan_msgs["end"] == 50

    ## Call it again with a different start value
    chan_msgs = requests.get(f"{BASE_URL}/channel/messages", params={
        "token": user1_token,
        "channel_id": ch1,
        "start": 50
    }).json()

    assert chan_msgs["start"] == 50
    assert chan_msgs["end"] == -1

def test_channel_messages_invalid():
    """
    A test for the channel/messages route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register user1 and user2
    _, user1_token = user1(PORT)
    _, user2_token = user2(PORT)

    ## Attempt to get channel messages for a nonexistent channel
    with pytest.raises(HTTPError):
        requests.get(f"{BASE_URL}/channel/messages", params={
            "token": user1_token,
            "channel_id": -999,
            "start": 0
        }).raise_for_status()

    ## user1 creates a channel
    ch1 = chan1(PORT, user1_token)

    ## Let user2 (not a member of channel1) attempt to get the channel's messages
    with pytest.raises(HTTPError):
        requests.get(f"{BASE_URL}/channel/messages", params={
            "token": user2_token,
            "channel_id": ch1,
            "start": 0
        }).raise_for_status()

    ## user1 sends a message
    requests.post(f"{BASE_URL}/message/send", json={
        "token": user1_token,
        "channel_id": ch1,
        "message": "user1's message"
    })

    ## Attempt to get channel messages with a start value of 5
    with pytest.raises(HTTPError):
        requests.get(f"{BASE_URL}/channel/messages", params={
            "token": user1_token,
            "channel_id": ch1,
            "start": 5 ## greater than or eq to number of messages
        }).raise_for_status()

    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.get(f"{BASE_URL}/channel/messages", params={
            "token": "11111",
            "channel_id": ch1,
            "start": 0
        }).raise_for_status()


####################################################################
##                     Testing channel/leave                      ##
####################################################################

def test_channel_leave_valid():
    """
    A test for the channel/leave route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register user1 and user2
    _, user1_token = user1(PORT)
    user2_id, user2_token = user2(PORT)

    ## user1 creates a channel and user2 joins the channel
    ch1 = chan1(PORT, user1_token)
    join_req(PORT, user2_token, ch1)

    ## user1 leaves the channel
    requests.post(f"{BASE_URL}/channel/leave", json={
        "token": user1_token,
        "channel_id": ch1
    })

    # Confirm that user1 has left using channel details
    response = requests.get(f"{BASE_URL}/channel/details", params={
        "token": user2_token,
        "channel_id": ch1
    }).json()
    assert response["all_members"] == [
        {
            "u_id": user2_id,
            "name_first": "Elon",
            "name_last": "Musk",
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        }
    ]

def test_channel_leave_invalid():
    """
    A test for the channel/leave route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register user1 and user2
    _, user1_token = user1(PORT)
    _, user2_token = user2(PORT)

    ## user1 attempts to leave a nonexistent channel
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/channel/leave", json={
            "token": user1_token,
            "channel_id": 999 ## invalid id
        }).raise_for_status()

    ## user1 creates a channel
    ch1 = chan1(PORT, user1_token)

    ## user2 (not a member of chan1) attempts to leave chan1
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/channel/leave", json={
            "token": user2_token,
            "channel_id": ch1
        }).raise_for_status()

    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/channel/leave", json={
            "token": "11111",
            "channel_id": ch1
        }).raise_for_status()


####################################################################
##                     Testing channel/join                       ##
####################################################################

def test_channel_join_valid():
    """
    A test for the channel/join route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register user1 and user2
    user1_id, user1_token = user1(PORT)
    user2_id, user2_token = user2(PORT)

    ## user1 creates a channel
    ch1 = chan1(PORT, user1_token)

    ## user2 joins channel1
    requests.post(f"{BASE_URL}/channel/join", json={
        "token": user2_token,
        "channel_id": ch1
    })

    ## Confirm that user2 has joined using channel details
    response = requests.get(f"{BASE_URL}/channel/details", params={
        "token": user1_token,
        "channel_id": ch1
    }).json()
    assert response["all_members"][0]["u_id"] == user1_id
    assert response["all_members"][1]["u_id"] == user2_id

def test_channel_join_invalid():
    """
    A test for the channel/join route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register user1 and user2
    _, user1_token = user1(PORT)
    _, user2_token = user2(PORT)

    ## user2 attempts to join a nonexistent channel
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/channel/join", json={
            "token": user2_token,
            "channel_id": -9999 ## invalid id
        }).raise_for_status()

    ## user1 creates a private channel
    response = requests.post(f"{BASE_URL}/channels/create", json={
        "token": user1_token,
        "name": "private channel",
        "is_public": False
    }).json()
    ch1 = response["channel_id"]

    ## user2 (a non-Slackr-owner) attempts to join a private channel
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/channel/join", json={
            "token": user2_token,
            "channel_id": ch1
        }).raise_for_status()

    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/channel/join", json={
            "token": "11111",
            "channel_id": ch1
        }).raise_for_status()


####################################################################
##                     Testing channel/addowner                   ##
####################################################################

def test_channel_addowner_valid():
    """
    A test for the channel/addowner route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register user1 and user2
    _, user1_token = user1(PORT)
    user2_id, user2_token = user2(PORT)

    ## user1 creates a channel
    ch1 = chan1(PORT, user1_token)

    ## user2 joins channel1
    join_req(PORT, user2_token, ch1)

    ## Promote user2 to an owner of channel1
    requests.post(f"{BASE_URL}/channel/addowner", json={
        "token": user1_token,
        "channel_id": ch1,
        "u_id": user2_id
    })

    ## Confirm user2 is an owner using channel_details
    response = requests.get(f"{BASE_URL}/channel/details", params={
        "token": user1_token,
        "channel_id": ch1
    }).json()

    owner_members = response["owner_members"]
    assert any(member["u_id"] == user2_id for member in owner_members)

def test_channel_addowner_invalid():
    """
    A test for the channel/addowner route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register user1, user2 and user3
    user1_id, user1_token = user1(PORT)
    user2_id, user2_token = user2(PORT)
    user3_id, user3_token = user3(PORT)

    ## user1 attempts to add an owner to a nonexistent channel
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/channel/addowner", json={
            "token": user1_token,
            "channel_id": 9999, ## invalid id
            "u_id": user2_id
        }).raise_for_status()

    ## user1 creates a channel and user2 and user3 join the channel
    ch1 = chan1(PORT, user1_token)
    join_req(PORT, user2_token, ch1)
    join_req(PORT, user3_token, ch1)

    ## Let user2 (a non-owner) attempt to promote user3 to an owner
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/channel/addowner", json={
            "token": user2_token,
            "channel_id": ch1,
            "u_id": user3_id
        }).raise_for_status()

    ## Make user2 an owner
    requests.post(f"{BASE_URL}/channel/addowner", json={
        "token": user1_token,
        "channel_id": ch1,
        "u_id": user2_id
    })
    ## Let user2 attempt to promote user1 (already an owner) to an owner
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/channel/addowner", json={
            "token": user2_token,
            "channel_id": ch1,
            "u_id": user1_id
        }).raise_for_status()

    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/channel/addowner", json={
            "token": "11111",
            "channel_id": ch1,
            "u_id": user3_id
        }).raise_for_status()


####################################################################
##                     Testing channel/removeowner                ##
####################################################################

def test_channel_removeowner_valid():
    """
    A test for the channel/removeowner route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register user1 and user2
    user1_id, user1_token = user1(PORT)
    user2_id, user2_token = user2(PORT)

    ## user1 creates a channel and user2 joins the channel
    ch1 = chan1(PORT, user1_token)
    join_req(PORT, user2_token, ch1)

    ## user1 promotes user2 to an owner
    requests.post(f"{BASE_URL}/channel/addowner", json={
        "token": user1_token,
        "channel_id": ch1,
        "u_id": user2_id
    })

    ## user1 now removes user2's ownership
    requests.post(f"{BASE_URL}/channel/removeowner", json={
        "token": user1_token,
        "channel_id": ch1,
        "u_id": user2_id
    })

    ## User channel details to check if user2 is no longer an owner
    response = requests.get(f"{BASE_URL}/channel/details", params={
        "token": user1_token,
        "channel_id": ch1
    }).json()
    owner_members = response["owner_members"]
    assert owner_members == [
        {
            "u_id": user1_id,
            "name_first": "Bob",
            "name_last": "Ross",
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        }
    ]

def test_channel_removeowner_invalid():
    """
    A test for the channel/removeowner route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register user1 and user2
    user1_id, user1_token = user1(PORT)
    user2_id, user2_token = user2(PORT)

    ## user1 attempts to remove ownership in a nonexistent channel
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/channel/removeowner", json={
            "token": user1_token,
            "channel_id": -9999, ## invalid id
            "u_id": user2_id
        }).raise_for_status()

    ## user1 creates a channel and user2 joins the channel
    ch1 = chan1(PORT, user1_token)
    join_req(PORT, user2_token, ch1)

    ## Let user2 (a non-owner) attempt to remove user1's ownership
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/channel/removeowner", json={
            "token": user2_token,
            "channel_id": ch1,
            "u_id": user1_id
        }).raise_for_status()

    ## Let user1 attempt to remove user2's ownership when user2 isn't an owner
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/channel/removeowner", json={
            "token": user1_token,
            "channel_id": ch1,
            "u_id": user2_id
        }).raise_for_status()

    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/channel/removeowner", json={
            "token": "11111",
            "channel_id": ch1,
            "u_id": user1_id
        }).raise_for_status()
