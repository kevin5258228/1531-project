"""
System tests for the message routes in server.py.
H11A-quadruples, April 2020.
"""

from datetime import datetime, timezone
import time
import requests
from requests.exceptions import HTTPError
import pytest
from helpers.registers_http import user1, user2, chan1
from port_settings import PORT, BASE_URL

####################################################################
##                     Testing message/send                       ##
####################################################################

def test_message_send_valid():
    """
    A test for the message/send route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    ## Register users and create a channel
    user1_id, user1_token = user1(PORT)
    ch1 = chan1(PORT, user1_token)

    ## Send a message and get a timestamp
    now = datetime.utcnow()
    timestamp = int(now.replace(tzinfo=timezone.utc).timestamp())
    response = requests.post(f"{BASE_URL}/message/send", json={
        "token": user1_token,
        "channel_id": ch1,
        "message": "This is a valid message"
    }).json()

    m_id = response["message_id"]

    ## Assert that the message has been sent
    messages = requests.get(f"{BASE_URL}/channel/messages", params={
        "token": user1_token,
        "channel_id": ch1,
        "start": 0
    }).json()

    assert messages["messages"] == [
        {
            "message_id": m_id,
            "u_id": user1_id,
            "message": "This is a valid message",
            "time_created": timestamp,
            "reacts": [],
            "is_pinned": False
        }
    ]

def test_message_send_invalid():
    """
    A test for the message/send route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    ## Register users and create a channel
    _, user1_token = user1(PORT)
    _, user2_token = user2(PORT)
    ch1 = chan1(PORT, user1_token)

    ## user2 has not yet joined channel1 and hence can't message
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/send", json={
            "token": user2_token,
            "channel_id": ch1,
            "message": "Invalid message"
        }).raise_for_status()

    ## Test that an exception is thrown for long messages
    long_msg = "f" * 1001
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/send", json={
            "token": user1_token,
            "channel_id": ch1,
            "message": long_msg
        }).raise_for_status()

    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/send", json={
            "token": "11111",
            "channel_id": ch1,
            "message": "hello"
        }).raise_for_status()


####################################################################
##                   Testing message/sendlater                    ##
####################################################################

def test_message_sendlater_valid():
    """
    A test for the message/sendlater route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    ## Register users and create a channel
    user1_id, user1_token = user1(PORT)
    ch1 = chan1(PORT, user1_token)

    ## Get the current time
    now = datetime.utcnow()
    time_now = int(now.replace(tzinfo=timezone.utc).timestamp())

    ## Send a message 5 seconds from now
    response = requests.post(f"{BASE_URL}/message/sendlater", json={
        "token": user1_token,
        "channel_id": ch1,
        "message": "hello",
        "time_sent": time_now + 5
    }).json()

    m_id = response["message_id"]

    ## Assert that the message hasn't been sent yet
    messages = requests.get(f"{BASE_URL}/channel/messages", params={
        "token": user1_token,
        "channel_id": ch1,
        "start": 0
    }).json()
    assert messages["messages"] == []

    ## Sleep for 5 seconds and assert that the message has been sent
    time.sleep(5)
    messages = requests.get(f"{BASE_URL}/channel/messages", params={
        "token": user1_token,
        "channel_id": ch1,
        "start": 0
    }).json()
    assert messages["messages"] == [
        {
            "message_id": m_id,
            "u_id": user1_id,
            "message": "hello",
            "time_created": time_now + 5,
            "reacts": [],
            "is_pinned": False
        }
    ]

def test_message_sendlater_invalid():
    """
    A test for the message/sendlater route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    ## Register users and create a channel
    _, user1_token = user1(PORT)
    _, user2_token = user2(PORT)
    ch1 = chan1(PORT, user1_token)

    ## Get the current time
    now = datetime.utcnow()
    time_now = int(now.replace(tzinfo=timezone.utc).timestamp())

    ## Attempt to sendlater in a nonexistent channel
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/sendlater", json={
            "token": user1_token,
            "channel_id": 9999, ## assumed to be an invalid channel_id
            "message": "hello",
            "time_sent": time_now + 5
        }).raise_for_status()

    ## Attempt to send a long message
    long_msg = "f" * 1001
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/sendlater", json={
            "token": user1_token,
            "channel_id": ch1,
            "message": long_msg,
            "time_sent": time_now + 5
        }).raise_for_status()

    ## user2 is not in chan1, so let user2 attempt to post in chan1
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/sendlater", json={
            "token": user2_token,
            "channel_id": ch1,
            "message": "hello",
            "time_sent": time_now + 5
        }).raise_for_status()

    ## Attempt to send with a time in the past
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/sendlater", json={
            "token": user1_token,
            "channel_id": ch1,
            "message": "hello",
            "time_sent": time_now - 999 ## a time in the past
        }).raise_for_status()

    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/sendlater", json={
            "token": "11111",
            "channel_id": ch1,
            "message": "hello",
            "time_sent": time_now + 5
        }).raise_for_status()


####################################################################
##                     Testing message/react                      ##
####################################################################

def test_message_react_valid():
    """
    A test for the message/react route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    ## Register users and create a channel
    user1_id, user1_token = user1(PORT)
    _, user2_token = user2(PORT)
    ch1 = chan1(PORT, user1_token)

    ## user1 sends a message
    response = requests.post(f"{BASE_URL}/message/send", json={
        "token": user1_token,
        "channel_id": ch1,
        "message": "This is a valid message"
    }).json()

    m_id = response["message_id"]

    ## user1 reacts to the message
    requests.post(f"{BASE_URL}/message/react", json={
        "token": user1_token,
        "message_id": m_id,
        "react_id": 1
    })

    ## Assert that the message is now reacted to
    messages = requests.get(f"{BASE_URL}/channel/messages", params={
        "token": user1_token,
        "channel_id": ch1,
        "start": 0
    }).json()
    assert messages["messages"][0]["reacts"] == [
        {
            "react_id": 1,
            "u_ids": [user1_id],
            "is_this_user_reacted": True
        }
    ]

    ## Let user2 join chan1
    requests.post(f"{BASE_URL}/channel/join", json={
        "token": user2_token,
        "channel_id": ch1
    })

    ## Assert that is_this_user_reacted is False for user2
    messages = requests.get(f"{BASE_URL}/channel/messages", params={
        "token": user2_token,
        "channel_id": ch1,
        "start": 0
    }).json()
    assert messages["messages"][0]["reacts"] == [
        {
            "react_id": 1,
            "u_ids": [user1_id],
            "is_this_user_reacted": False
        }
    ]

def test_message_react_invalid():
    """
    A test for the message/react route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    ## Register users and create a channel
    _, user1_token = user1(PORT)
    _, user2_token = user2(PORT)
    ch1 = chan1(PORT, user1_token)

    ## user1 sends a message
    response = requests.post(f"{BASE_URL}/message/send", json={
        "token": user1_token,
        "channel_id": ch1,
        "message": "This is a valid message"
    }).json()

    m_id = response["message_id"]

    ## Attempt to react with an invalid react_id
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/react", json={
            "token": user1_token,
            "message_id": m_id,
            "react_id": 9999
        }).raise_for_status()

    ## user2 is not in chan1 so let user2 attempt to react to m_id
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/react", json={
            "token": user2_token,
            "message_id": m_id,
            "react_id": 1
        }).raise_for_status()

    ## Let user1 react to their message and attempt to react again
    requests.post(f"{BASE_URL}/message/react", json={
        "token": user1_token,
        "message_id": m_id,
        "react_id": 1
    })
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/react", json={
            "token": user1_token,
            "message_id": m_id,
            "react_id": 1
        }).raise_for_status()

    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/react", json={
            "token": "11111",
            "message_id": m_id,
            "react_id": 1
        }).raise_for_status()


####################################################################
##                    Testing message/unreact                     ##
####################################################################

def test_message_unreact_valid():
    """
    A test for the message/unreact route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    ## Register users and create a channel
    user1_id, user1_token = user1(PORT)
    ch1 = chan1(PORT, user1_token)

    ## user1 sends a message
    response = requests.post(f"{BASE_URL}/message/send", json={
        "token": user1_token,
        "channel_id": ch1,
        "message": "This is a valid message"
    }).json()

    m_id = response["message_id"]

    ## user1 reacts to the message
    requests.post(f"{BASE_URL}/message/react", json={
        "token": user1_token,
        "message_id": m_id,
        "react_id": 1
    })

    ## Assert that the message is now reacted to
    messages = requests.get(f"{BASE_URL}/channel/messages", params={
        "token": user1_token,
        "channel_id": ch1,
        "start": 0
    }).json()
    assert messages["messages"][0]["reacts"] == [
        {
            "react_id": 1,
            "u_ids": [user1_id],
            "is_this_user_reacted": True
        }
    ]

    ## user1 unreacts the message
    requests.post(f"{BASE_URL}/message/unreact", json={
        "token": user1_token,
        "message_id": m_id,
        "react_id": 1
    })

    ## Assert that the react is no longer there
    messages = requests.get(f"{BASE_URL}/channel/messages", params={
        "token": user1_token,
        "channel_id": ch1,
        "start": 0
    }).json()
    assert messages["messages"][0]["reacts"] == []

def test_message_unreact_invalid():
    """
    A test for the message/unreact route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    ## Register users and create a channel
    _, user1_token = user1(PORT)
    _, user2_token = user2(PORT)
    ch1 = chan1(PORT, user1_token)

    ## user1 sends a message
    response = requests.post(f"{BASE_URL}/message/send", json={
        "token": user1_token,
        "channel_id": ch1,
        "message": "This is a valid message"
    }).json()

    m_id = response["message_id"]

    ## Attempt to unreact with an invalid react_id
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/unreact", json={
            "token": user1_token,
            "message_id": m_id,
            "react_id": 9999 # invalid
        }).raise_for_status()

    ## Attempt to react to a message that the user has not reacted to
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/unreact", json={
            "token": user1_token,
            "message_id": m_id,
            "react_id": 1
        }).raise_for_status()

    ## Let user2 attempt to react to a message in chan1 which they aren't in
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/unreact", json={
            "token": user2_token,
            "message_id": m_id,
            "react_id": 1
        }).raise_for_status()

    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/unreact", json={
            "token": "11111",
            "message_id": m_id,
            "react_id": 1
        }).raise_for_status()


####################################################################
##                       Testing message/pin                      ##
####################################################################

def test_message_pin_valid():
    """
    A test for the message/pin route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    ## Register users and create a channel
    _, user1_token = user1(PORT)
    ch1 = chan1(PORT, user1_token)

    ## user1 sends a message
    response = requests.post(f"{BASE_URL}/message/send", json={
        "token": user1_token,
        "channel_id": ch1,
        "message": "This is a valid message"
    }).json()

    m_id = response["message_id"]

    ## Check the message isn't pinned by default
    messages = requests.get(f"{BASE_URL}/channel/messages", params={
        "token": user1_token,
        "channel_id": ch1,
        "start": 0
    }).json()
    assert not messages["messages"][0]["is_pinned"]

    ## user1 pins the message
    requests.post(f"{BASE_URL}/message/pin", json={
        "token": user1_token,
        "message_id": m_id
    })

    ## Assert that the message is now pinned
    messages = requests.get(f"{BASE_URL}/channel/messages", params={
        "token": user1_token,
        "channel_id": ch1,
        "start": 0
    }).json()
    assert messages["messages"][0]["is_pinned"]

def test_message_pin_invalid():
    """
    A test for the message/pin route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    ## Register users and create a channel
    _, user1_token = user1(PORT)
    _, user2_token = user2(PORT)
    ch1 = chan1(PORT, user1_token)

    ## Attempt to pin a message that does not exist
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/pin", json={
            "token": user1_token,
            "message_id": 9999 ## invalid id
        }).raise_for_status()

    ## user1 sends a message
    response = requests.post(f"{BASE_URL}/message/send", json={
        "token": user1_token,
        "channel_id": ch1,
        "message": "This is a valid message"
    }).json()

    m_id = response["message_id"]

    ## Let user2 try to pin a message in a channel they are not in
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/pin", json={
            "token": user2_token,
            "message_id": m_id
        }).raise_for_status()

    ## user2 joins chan1
    requests.post(f"{BASE_URL}/channel/join", json={
        "token": user2_token,
        "channel_id": ch1
    })

    ## Let user2 (a non-owner of chan1) try to pin a message
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/pin", json={
            "token": user2_token,
            "message_id": m_id
        }).raise_for_status()

    ## Let user1 pin the message and attempt to pin it again
    requests.post(f"{BASE_URL}/message/pin", json={
        "token": user1_token,
        "message_id": m_id
    })
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/pin", json={
            "token": user1_token,
            "message_id": m_id
        }).raise_for_status()

    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/pin", json={
            "token": "11111",
            "message_id": m_id
        }).raise_for_status()


####################################################################
##                      Testing message/unpin                     ##
####################################################################

def test_message_unpin_valid():
    """
    A test for the message/unpin route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    ## Register users and create a channel
    _, user1_token = user1(PORT)
    ch1 = chan1(PORT, user1_token)

    ## user1 sends a message
    response = requests.post(f"{BASE_URL}/message/send", json={
        "token": user1_token,
        "channel_id": ch1,
        "message": "This is a valid message"
    }).json()

    m_id = response["message_id"]

    ## user1 pins the message
    requests.post(f"{BASE_URL}/message/pin", json={
        "token": user1_token,
        "message_id": m_id
    })

    ## Assert that the message is now pinned
    messages = requests.get(f"{BASE_URL}/channel/messages", params={
        "token": user1_token,
        "channel_id": ch1,
        "start": 0
    }).json()
    assert messages["messages"][0]["is_pinned"]

    ## user1 unpins the message
    requests.post(f"{BASE_URL}/message/unpin", json={
        "token": user1_token,
        "message_id": m_id
    })

    ## Assert that the message is no longer pinned
    messages = requests.get(f"{BASE_URL}/channel/messages", params={
        "token": user1_token,
        "channel_id": ch1,
        "start": 0
    }).json()
    assert not messages["messages"][0]["is_pinned"]

def test_message_unpin_invalid():
    """
    A test for the message/unpin route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    ## Register users and create a channel
    _, user1_token = user1(PORT)
    _, user2_token = user2(PORT)
    ch1 = chan1(PORT, user1_token)

    ## Attempt to unpin a nonexistent message
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/unpin", json={
            "token": user1_token,
            "message_id": 9999 ## invalid id
        }).raise_for_status()

    ## user1 sends a message
    response = requests.post(f"{BASE_URL}/message/send", json={
        "token": user1_token,
        "channel_id": ch1,
        "message": "This is a valid message"
    }).json()

    m_id = response["message_id"]

    ## Let user2 (who is not in chan1) attempt to unpin the message
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/unpin", json={
            "token": user2_token,
            "message_id": m_id
        }).raise_for_status()

    ## user2 joins chan1
    requests.post(f"{BASE_URL}/channel/join", json={
        "token": user2_token,
        "channel_id": ch1
    })

    ## user1 pins the message
    requests.post(f"{BASE_URL}/message/pin", json={
        "token": user1_token,
        "message_id": m_id
    })

    ## Let user2 (a non-owner of chan1) try to unpin the message
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/unpin", json={
            "token": user2_token,
            "message_id": m_id
        }).raise_for_status()

    ## Let user1 unpin the message and attempt to unpin it again
    requests.post(f"{BASE_URL}/message/unpin", json={
        "token": user1_token,
        "message_id": m_id
    })
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/unpin", json={
            "token": user1_token,
            "message_id": m_id
        }).raise_for_status()

    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.post(f"{BASE_URL}/message/unpin", json={
            "token": "11111",
            "message_id": m_id
        }).raise_for_status()


####################################################################
##                     Testing message/remove                     ##
####################################################################

def test_message_remove_valid():
    """
    A test for the message/remove route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    ## Register users and create a channel
    _, user1_token = user1(PORT)
    ch1 = chan1(PORT, user1_token)

    ## user1 sends a message
    response = requests.post(f"{BASE_URL}/message/send", json={
        "token": user1_token,
        "channel_id": ch1,
        "message": "This is a valid message"
    }).json()

    m_id = response["message_id"]

    ## Check the message has been sent
    messages = requests.get(f"{BASE_URL}/channel/messages", params={
        "token": user1_token,
        "channel_id": ch1,
        "start": 0
    }).json()
    assert messages["messages"][0]["message_id"] == m_id

    ## Remove the message
    requests.delete(f"{BASE_URL}/message/remove", json={
        "token": user1_token,
        "message_id": m_id
    })

    ## Check that the message has been removed
    messages = requests.get(f"{BASE_URL}/channel/messages", params={
        "token": user1_token,
        "channel_id": ch1,
        "start": 0
    }).json()
    assert messages["messages"] == []

def test_message_remove_invalid():
    """
    A test for the message/remove route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    ## Register users and create a channel
    _, user1_token = user1(PORT)
    _, user2_token = user2(PORT)
    ch1 = chan1(PORT, user1_token)

    ## Attempt to remove a message with invalid id
    with pytest.raises(HTTPError):
        requests.delete(f"{BASE_URL}/message/remove", json={
            "token": user1_token,
            "message_id": 9999 ## invalid id
        }).raise_for_status()

    ## user1 sends a message
    response = requests.post(f"{BASE_URL}/message/send", json={
        "token": user1_token,
        "channel_id": ch1,
        "message": "This is a valid message"
    }).json()

    m_id = response["message_id"]

    ## user2 joins chan1
    requests.post(f"{BASE_URL}/channel/join", json={
        "token": user2_token,
        "channel_id": ch1
    })

    ## Let user2 (a non-owner) attempt to delete user1's message
    with pytest.raises(HTTPError):
        requests.delete(f"{BASE_URL}/message/remove", json={
            "token": user2_token,
            "message_id": m_id
        }).raise_for_status()

    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.delete(f"{BASE_URL}/message/remove", json={
            "token": "11111",
            "message_id": m_id
        }).raise_for_status()


####################################################################
##                      Testing message/edit                      ##
####################################################################

def test_message_edit_valid():
    """
    A test for the message/edit route under valid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    ## Register users and create a channel
    _, user1_token = user1(PORT)
    ch1 = chan1(PORT, user1_token)

    ## user1 sends a message
    response = requests.post(f"{BASE_URL}/message/send", json={
        "token": user1_token,
        "channel_id": ch1,
        "message": "This is a valid message"
    }).json()

    m_id = response["message_id"]

    ## Check the message string
    messages = requests.get(f"{BASE_URL}/channel/messages", params={
        "token": user1_token,
        "channel_id": ch1,
        "start": 0
    }).json()
    assert messages["messages"][0]["message"] == "This is a valid message"

    ## user1 edits the message
    requests.put(f"{BASE_URL}/message/edit", json={
        "token": user1_token,
        "message_id": m_id,
        "message": "new message"
    })

    ## Check that the message string has updated
    messages = requests.get(f"{BASE_URL}/channel/messages", params={
        "token": user1_token,
        "channel_id": ch1,
        "start": 0
    }).json()
    assert messages["messages"][0]["message"] == "new message"

    ## user1 edits the message with an empty string
    requests.put(f"{BASE_URL}/message/edit", json={
        "token": user1_token,
        "message_id": m_id,
        "message": ""
    })

    ## Check that the message has been deleted
    messages = requests.get(f"{BASE_URL}/channel/messages", params={
        "token": user1_token,
        "channel_id": ch1,
        "start": 0
    }).json()
    assert messages["messages"] == []

def test_message_edit_invalid():
    """
    A test for the message/edit route under invalid input.
    """
    requests.post(f"{BASE_URL}/workspace/reset")
    ## Register users and create a channel
    _, user1_token = user1(PORT)
    _, user2_token = user2(PORT)
    ch1 = chan1(PORT, user1_token)

    ## user1 sends a message
    response = requests.post(f"{BASE_URL}/message/send", json={
        "token": user1_token,
        "channel_id": ch1,
        "message": "This is a valid message"
    }).json()

    m_id = response["message_id"]

    ## Let user2 (non-owner) join chan1 and attempt to edit user1's message
    requests.post(f"{BASE_URL}/channel/join", json={
        "token": user2_token,
        "channel_id": ch1
    })
    with pytest.raises(HTTPError):
        requests.put(f"{BASE_URL}/message/edit", json={
            "token": user2_token,
            "message_id": m_id,
            "message": "hello"
        }).raise_for_status()

    ## Errors for invalid tokens
    with pytest.raises(HTTPError):
        requests.put(f"{BASE_URL}/message/edit", json={
            "token": "11111",
            "message_id": m_id,
            "message": "hello"
        }).raise_for_status()
