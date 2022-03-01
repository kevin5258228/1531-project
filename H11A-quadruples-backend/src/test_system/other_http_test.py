"""
System tests for the other routes in server.py.
H11A-quadruples, April 2020.
"""

from datetime import datetime, timezone
import time
import requests
from requests.exceptions import HTTPError
import pytest
from helpers.registers_http import user1, user2, user3, chan1, chan2, chan3, join_req
from port_settings import PORT, BASE_URL

####################################################################
##                      Testing users/all                         ##
####################################################################

def test_users_all_one():
    """
    A test for the users/all route under a VALID input of one user.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    user1_id, user1_token = user1(PORT)

    ## Test if users_all() returns the correct dictionary for user1
    ## Should return a dictionary containing a list containing a dictionary
    response = requests.get(f"{BASE_URL}/users/all", params={
        "token": user1_token
    }).json()
    assert response == {
        'users': [
            {
                'u_id': user1_id,
                'email': 'bob.ross@unsw.edu.au',
                'name_first': 'Bob',
                'name_last': 'Ross',
                'handle_str': 'bobross',
                'profile_img_url': f"{BASE_URL}/imgurl/default.jpg"
            }
        ]
    }

def test_users_all_two():
    """
    A test for the users/all route under a VALID input of two users.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    user1_id, user1_token = user1(PORT)
    user2_id, user2_token = user2(PORT)

    ## Test if users_all() returns the correct dictionary for users 1 & 2
    ## Should return a dictionary containing a list containing dictionaries
    response1 = requests.get(f"{BASE_URL}/users/all", params={
        "token": user1_token
    }).json()
    response2 = requests.get(f"{BASE_URL}/users/all", params={
        "token": user2_token
    }).json()
    assert response1 == {
        'users': [
            {
                'u_id': user1_id,
                'email': 'bob.ross@unsw.edu.au',
                'name_first': 'Bob',
                'name_last': 'Ross',
                'handle_str': 'bobross',
                'profile_img_url': f"{BASE_URL}/imgurl/default.jpg"
            },
            {
                'u_id': user2_id,
                'email': 'elon.musk@unsw.edu.au',
                'name_first': 'Elon',
                'name_last': 'Musk',
                'handle_str': 'elonmusk',
                'profile_img_url': f"{BASE_URL}/imgurl/default.jpg"
            }
        ]
    }
    ## The user list should be the same regardless of who makes the request
    assert response1 == response2

def test_users_all_other():
    """
    A test for the users/all route under a VALID input of three users.
    Also calls a variety of user routes to test if users/all updates
    whenever a user updates their information.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    user1_id, user1_token = user1(PORT)
    user2_id, user2_token = user2(PORT)
    user3_id, user3_token = user3(PORT)

    ## Test if users_all() returns the correct dictionary BEFORE calling
    ## any user_profile functions
    response1 = requests.get(f"{BASE_URL}/users/all", params={
        "token": user1_token
    }).json()
    assert response1 == {
        'users': [
            {
                'u_id': user1_id,
                'email': 'bob.ross@unsw.edu.au',
                'name_first': 'Bob',
                'name_last': 'Ross',
                'handle_str': 'bobross',
                'profile_img_url': f"{BASE_URL}/imgurl/default.jpg"
            },
            {
                'u_id': user2_id,
                'email': 'elon.musk@unsw.edu.au',
                'name_first': 'Elon',
                'name_last': 'Musk',
                'handle_str': 'elonmusk',
                'profile_img_url': f"{BASE_URL}/imgurl/default.jpg"
            },
            {
                'u_id': user3_id,
                'email': 'steve.jobs@unsw.edu.au',
                'name_first': 'Steve',
                'name_last': 'Jobs',
                'handle_str': 'stevejobs',
                'profile_img_url': f"{BASE_URL}/imgurl/default.jpg"
            }
        ]
    }
    ## Again, the user list should be the same regardless of who
    ## makes the request
    response2 = requests.get(f"{BASE_URL}/users/all", params={
        "token": user2_token
    }).json()
    response3 = requests.get(f"{BASE_URL}/users/all", params={
        "token": user3_token
    }).json()
    assert response1 == response2
    assert response2 == response3

    ## The following assumes user/profile/setname, user/profile/setemail
    ## and user/profile/sethandle routes are all functional
    requests.put(f"{BASE_URL}/user/profile/setname", json={
        "token": user1_token,
        "name_first": 'Ross',
        "name_last": 'Bob'
    })
    requests.put(f"{BASE_URL}/user/profile/setemail", json={
        "token": user2_token,
        "email": 'elon.musk@gmail.com'
    })
    requests.put(f"{BASE_URL}/user/profile/sethandle", json={
        "token": user3_token,
        "handle_str": 'jobssteve'
    })

    data = requests.get(f"{BASE_URL}/users/all", params={
        "token": user1_token
    }).json()
    ## Test if users_all() updates with these changes just made
    assert data == {
        'users': [
            {
                'u_id': user1_id,
                'email': 'bob.ross@unsw.edu.au',
                'name_first': 'Ross',
                'name_last': 'Bob',
                'handle_str': 'bobross',
                'profile_img_url': f"{BASE_URL}/imgurl/default.jpg"
            },
            {
                'u_id': user2_id,
                'email': 'elon.musk@gmail.com',
                'name_first': 'Elon',
                'name_last': 'Musk',
                'handle_str': 'elonmusk',
                'profile_img_url': f"{BASE_URL}/imgurl/default.jpg"
            },
            {
                'u_id': user3_id,
                'email': 'steve.jobs@unsw.edu.au',
                'name_first': 'Steve',
                'name_last': 'Jobs',
                'handle_str': 'jobssteve',
                'profile_img_url': f"{BASE_URL}/imgurl/default.jpg"
            }
        ]
    }

def test_users_all_invalid():
    """
    A test for the users/all route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.get(f"{BASE_URL}/users/all", params={
            "token": "11111"
        }).raise_for_status()


####################################################################
##                        Testing search                          ##
####################################################################

def test_search_non_empty_result():
    """
    A test for the search route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register users 1 and 2
    _, user1_token = user1(PORT)
    _, user2_token = user2(PORT)

    ## Users 1 creates two different channels
    channel_id1 = chan1(PORT, user1_token)
    channel_id2 = chan2(PORT, user1_token)

    ## User 2 joins the two different channels
    join_req(PORT, user2_token, channel_id1)
    join_req(PORT, user2_token, channel_id2)

    ## User 2 sends a message to first channel
    requests.post(f"{BASE_URL}/message/send", json={
        "token": user2_token,
        "channel_id": channel_id1,
        "message": "Hello world"
    }).json()

    ## User 2 then sends a message to the second channel
    requests.post(f"{BASE_URL}/message/send", json={
        "token": user2_token,
        "channel_id": channel_id2,
        "message": "Hello world"
    }).json()

    ## Get details of messages from the two channels
    data1 = requests.get(f"{BASE_URL}/channel/messages", params={
        "token": user2_token,
        "channel_id": channel_id1,
        "start": 0
    }).json()

    data2 = requests.get(f"{BASE_URL}/channel/messages", params={
        "token": user2_token,
        "channel_id": channel_id2,
        "start": 0
    }).json()

    list_messages1 = data1["messages"]
    list_messages2 = data2["messages"]
    joined_list = list_messages2 + list_messages1

    ## Check that search returns the correct list of messages
    result = requests.get(f"{BASE_URL}/search", params={
        "token": user2_token,
        "query_str": "Hello world"
    }).json()
    list_messages = result["messages"]
    ## Most recent to least recent
    assert list_messages == joined_list

def test_search_empty_result():
    """
    A test for the search route under other valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register users 1 and 2
    _, user1_token = user1(PORT)
    _, user2_token = user2(PORT)

    ## Users 1 creates two different channels
    channel_id1 = chan1(PORT, user1_token)
    channel_id2 = chan2(PORT, user1_token)

    ## User 2 joins the two different channels
    join_req(PORT, user2_token, channel_id1)
    join_req(PORT, user2_token, channel_id2)

    ## User 2 sends a message to first channel
    requests.post(f"{BASE_URL}/message/send", json={
        "token": user2_token,
        "channel_id": channel_id1,
        "message": "Hello world"
    }).json()

    ## User 2 then sends a message to the second channel
    requests.post(f"{BASE_URL}/message/send", json={
        "token": user2_token,
        "channel_id": channel_id1,
        "message": "I love python"
    }).json()

    ## Assert that a search for "COMP1531" returns an empty list
    result = requests.get(f"{BASE_URL}/search", params={
        "token": user2_token,
        "query_str": "COMP1531"
    }).json()
    list_messages = result['messages']
    assert list_messages == []

def test_search_invalid():
    """
    A test for the search route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.get(f"{BASE_URL}/search", params={
            "token": "11111",
            "query_str": "COMP1531"
        }).raise_for_status()


####################################################################
##                       Testing standup/*                        ##
####################################################################

def test_standup_valid():
    """
    A test for the standup routes under valid inputs.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Register users 1, 2, 3
    user1_id, user1_token = user1(PORT)
    _, user2_token = user2(PORT)
    _, user3_token = user3(PORT)

    ## User 1 creates a channel
    channel_id1 = chan1(PORT, user1_token)

    ## Users 2 and 3 join the channel
    join_req(PORT, user2_token, channel_id1)
    join_req(PORT, user3_token, channel_id1)

    ## Assert standup_active is false
    response = requests.get(f"{BASE_URL}/standup/active", params={
        "token": user1_token,
        "channel_id": channel_id1
    }).json()
    assert response == {
        "is_active": False,
        "time_finish": None
    }

    ## Find the time_now and start the standup
    now = datetime.utcnow()
    time_now = int(now.replace(tzinfo=timezone.utc).timestamp())
    data = requests.post(f"{BASE_URL}/standup/start", json={
        "token": user1_token,
        "channel_id": channel_id1,
        "length": 10
    }).json()
    time_finish = data["time_finish"]
    assert time_finish == time_now + 10

    ## Assert standup_active is true
    response = requests.get(f"{BASE_URL}/standup/active", params={
        "token": user1_token,
        "channel_id": channel_id1
    }).json()
    assert response == {
        "is_active": True,
        "time_finish": time_now + 10
    }

    ## Send some messages in the standup
    requests.post(f"{BASE_URL}/standup/send", json={
        "token": user1_token,
        "channel_id": channel_id1,
        "message": "user1 msg1"
    }).json()
    requests.post(f"{BASE_URL}/standup/send", json={
        "token": user1_token,
        "channel_id": channel_id1,
        "message": "user1 msg2"
    }).json()
    requests.post(f"{BASE_URL}/standup/send", json={
        "token": user2_token,
        "channel_id": channel_id1,
        "message": "user2 msg1"
    }).json()
    time.sleep(5)
    requests.post(f"{BASE_URL}/standup/send", json={
        "token": user2_token,
        "channel_id": channel_id1,
        "message": "user2 msg2"
    }).json()
    requests.post(f"{BASE_URL}/standup/send", json={
        "token": user3_token,
        "channel_id": channel_id1,
        "message": "user3 msg1"
    }).json()

    ## Check channel_messages before standup finishes
    message_result = requests.get(f"{BASE_URL}/channel/messages", params={
        "token": user1_token,
        "channel_id": channel_id1,
        "start": 0
    }).json()
    assert message_result["messages"] == []
    time.sleep(5)

    ## Check channel_messages
    expected_msg = """bob: user1 msg1\n\
bob: user1 msg2\n\
elon: user2 msg1\n\
elon: user2 msg2\n\
steve: user3 msg1\n"""
    payload = requests.get(f"{BASE_URL}/channel/messages", params={
        "token": user1_token,
        "channel_id": channel_id1,
        "start": 0
    }).json()
    assert payload == {
        "messages": [
            {
                "message_id": 1, ## first message
                "u_id": user1_id, ## since user1 initiated standup
                "message": expected_msg,
                "time_created": time_now + 10,
                "reacts": [],
                "is_pinned": False
            }
        ],
        "start": 0,
        "end": -1
    }

def test_standup_start_invalid():
    """
    A test for the standup/start route under invalid inputs.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    _, user1_token = user1(PORT)

    ## Channel does not exist
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/standup/start", json={
            "token": user1_token,
            "channel_id": 1,
            "length": 10
        }).raise_for_status()

    ## Begin a standup and attempt to start another one
    channel_id1 = chan1(PORT, user1_token)
    requests.post(f"{BASE_URL}/standup/start", json={
        "token": user1_token,
        "channel_id": channel_id1,
        "length": 5
    })
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/standup/start", json={
            "token": user1_token,
            "channel_id": channel_id1,
            "length": 5
        }).raise_for_status()

    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/standup/start", json={
            "token": "11111",
            "channel_id": channel_id1,
            "length": 5
        }).raise_for_status()

def test_standup_active_invalid():
    """
    A test for the standup/active route under invalid inputs.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    _, user1_token = user1(PORT)

    ## Channel does not exist
    with pytest.raises(HTTPError):
        requests.get(f"{BASE_URL}/standup/active", params={
            "token": user1_token,
            "channel_id": 1
        }).raise_for_status()

    ## Errors for invalid tokens
    ch1 = chan1(PORT, user1_token)
    with pytest.raises(HTTPError):
        requests.get(f"{BASE_URL}/standup/active", params={
            "token": "11111",
            "channel_id": ch1
        }).raise_for_status()

def test_standup_send_invalid():
    """
    A test for the standup/send route under invalid inputs.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    _, user1_token = user1(PORT)
    _, user2_token = user2(PORT)

    ## Channel does not exist
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/standup/send", json={
            "token": user1_token,
            "channel_id": 1,
            "message": "hello"
        }).raise_for_status()

    ## Create the channel
    channel_id1 = chan1(PORT, user1_token)

    ## An active standup is not currently running
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/standup/send", json={
            "token": user1_token,
            "channel_id": channel_id1,
            "message": "hello"
        }).raise_for_status()

    ## User2 is not a member of chan1
    ## Start a standup
    requests.post(f"{BASE_URL}/standup/start", json={
        "token": user1_token,
        "channel_id": channel_id1,
        "length": 1
    }).json()

    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/standup/send", json={
            "token": user2_token,
            "channel_id": channel_id1,
            "message": "hello"
        }).raise_for_status()

    ## Message too long
    long_msg = "f" * 1001
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/standup/send", json={
            "token": user1_token,
            "channel_id": channel_id1,
            "message": long_msg
        }).raise_for_status()

    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/standup/send", json={
            "token": "11111",
            "channel_id": channel_id1,
            "message": "hi"
        }).raise_for_status()


####################################################################
##               Testing admin/userpermission/change              ##
####################################################################

def test_admin_userpermission_change_valid():
    """
    A test for the admin/userpermission/change route under valid inputs.
    """
    requests.post(f"{BASE_URL}/workspace/reset")

    user1_id, user1_token = user1(PORT)
    user2_id, user2_token = user2(PORT)
    channel_id1 = chan1(PORT, user1_token)
    channel_id2 = chan2(PORT, user2_token)

    ## Set user2 to be a Slackr owner
    requests.post(f"{BASE_URL}/admin/userpermission/change", json={
        "token": user1_token,
        "u_id": user2_id,
        "permission_id": 1
    })

    ## user2 joins chan1 and should be an owner
    requests.post(f"{BASE_URL}/channel/join", json={
        "token": user2_token,
        "channel_id": channel_id1
    })
    response = requests.get(f"{BASE_URL}/channel/details", params={
        "token": user2_token,
        "channel_id": channel_id1
    }).json()
    assert response['owner_members'] == [
        {
            "u_id": user1_id,
            "name_first": "Bob",
            "name_last": "Ross",
            'profile_img_url': f"{BASE_URL}/imgurl/default.jpg"
        },
        {
            "u_id": user2_id,
            "name_first": "Elon",
            "name_last": "Musk",
            'profile_img_url': f"{BASE_URL}/imgurl/default.jpg"
        }
    ]

    ## Set user1 to be a Slackr member
    requests.post(f"{BASE_URL}/admin/userpermission/change", json={
        "token": user2_token,
        "u_id": user1_id,
        "permission_id": 2
    })

    ## User1 joins chan2 and should NOT be an owner
    requests.post(f"{BASE_URL}/channel/join", json={
        "token": user1_token,
        "channel_id": channel_id2
    })
    response = requests.get(f"{BASE_URL}/channel/details", params={
        "token": user1_token,
        "channel_id": channel_id2
    }).json()
    assert response['owner_members'] == [
        {
            "u_id": user2_id,
            "name_first": "Elon",
            "name_last": "Musk",
            'profile_img_url': f"{BASE_URL}/imgurl/default.jpg"
        }
    ]

def test_admin_userpermission_change_invalid():
    """
    A test for the admin/userpermission/change route under invalid inputs.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    user1_id, user1_token = user1(PORT)

    ## User2 does not exist - assumed 99 is an invalid user
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/admin/userpermission/change", json={
            "token": user1_token,
            "u_id": 99,
            "permission_id": 1
        }).raise_for_status()

    ## Invalid permission_id - 99 is not a valid permission_id
    user2_id, user2_token = user2(PORT)
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/admin/userpermission/change", json={
            "token": user1_token,
            "u_id": user2_id,
            "permission_id": 99
        }).raise_for_status()

    ## User2 is not a Slackr owner and is therefore not authorised
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/admin/userpermission/change", json={
            "token": user2_token,
            "u_id": user1_id,
            "permission_id": 2
        }).raise_for_status()

    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/admin/userpermission/change", json={
            "token": "11111",
            "u_id": user1_id,
            "permission_id": 2
        }).raise_for_status()


####################################################################
##                     Testing admin/user/remove                  ##
####################################################################

def test_admin_user_remove_valid():
    """
    A test for the admin/user/remove route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    _, user1_token = user1(PORT)
    user2_id, _ = user2(PORT)

    ## user1 removes user2
    requests.delete(f"{BASE_URL}/admin/user/remove", params={
        "token": user1_token,
        "u_id": user2_id
    })

    ## Check that the user got deleted
    response = requests.get(f"{BASE_URL}/users/all", params={
        "token": user1_token
    }).json()
    assert all(user["u_id"] != user2_id for user in response["users"])

def test_admin_user_remove_invalid():
    """
    A test for the admin/user/remove route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    user1_id, user1_token = user1(PORT)
    user2_id, user2_token = user2(PORT)

    ## user1 attempts to remove a nonexistent user
    with pytest.raises(HTTPError):
        requests.delete(f"{BASE_URL}/admin/user/remove", params={
            "token": user1_token,
            "u_id": -9999 ## invalid id
        }).raise_for_status()

    ## user2, a non-owner, attempts to remove user1
    with pytest.raises(HTTPError):
        requests.delete(f"{BASE_URL}/admin/user/remove", params={
            "token": user2_token,
            "u_id": user1_id
        }).raise_for_status()

    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.delete(f"{BASE_URL}/admin/user/remove", params={
            "token": -9999, ## invalid token
            "u_id": user2_id
        }).raise_for_status()


####################################################################
##                    Testing workspace/reset                     ##
####################################################################

def test_workspace_reset():
    """
    A test for the workspace/reset route.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    ## Register some users
    _, user1_token = user1(PORT)
    _, user2_token = user2(PORT)
    _, user3_token = user3(PORT)

    ## Create some channels
    channel_id1 = chan1(PORT, user1_token)
    chan2(PORT, user2_token)
    chan3(PORT, user3_token)

    ## Send a message to channel 1
    requests.post(f"{BASE_URL}/message/send", json={
        "token": user1_token,
        "channel_id": channel_id1,
        "message": "Hello world"
    })

    ## Reset the workspace
    requests.post(f"{BASE_URL}/workspace/reset")

    ## Assert that there are no more users, channels and messages
    ## Token should not exist anymore
    with pytest.raises(HTTPError):
        requests.get(f"{BASE_URL}/users/all", params={
            "token": user1_token
        }).raise_for_status()

    with pytest.raises(HTTPError):
        requests.get(f"{BASE_URL}/channels/listall", params={
            "token": user1_token
        }).raise_for_status()

    with pytest.raises(HTTPError):
        requests.get(f"{BASE_URL}/channel/messages", params={
            "token": user1_token,
            "channel_id": channel_id1,
            "start": 0
        }).raise_for_status()
