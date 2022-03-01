"""
Integration tests for the functions implemented in message.py.
H11A-quadruples, April 2020.
"""

from datetime import datetime, timezone
import time
import pytest
from error import InputError, AccessError
from funcs.message import (
    message_send,
    message_sendlater,
    message_react,
    message_unreact,
    message_pin,
    message_unpin,
    message_remove,
    message_edit
)
from funcs.channel import channel_messages, channel_join
from funcs.other import workspace_reset
from helpers.registers import user1, user2, chan1, chan2

####################################################################
##                     Testing message_send                       ##
####################################################################

def test_message_send_valid_input():
    """
    A test for the message_send() function under valid input.
    """
    workspace_reset()
    _, user1_token = user1()
    ch1 = chan1(user1_token)
    ## Get the message_id from message_send()
    valid_message = message_send(user1_token, ch1, "This is a valid message")
    m_id1 = valid_message["message_id"]
    ## Assume channel_messages() works
    ## Get the message_id from channel_messages()
    m_id2 = channel_messages(user1_token, ch1, 0)["messages"][0]["message_id"]
    ## Check that these id"s are the same
    assert m_id1 == m_id2

def test_message_send_too_long():
    """
    A test for the message_send() function to check that an InputError is
    thrown when the message is over 1000 characters.
    """
    workspace_reset()
    _, user1_token = user1()
    ch1 = chan1(user1_token)
    ## Generate two messages that are over 1000 characters long
    long_message1 = "f" * 2000
    long_message2 = " " * 1001
    with pytest.raises(InputError):
        message_send(user1_token, ch1, long_message1)
    with pytest.raises(InputError):
        message_send(user1_token, ch1, long_message2)

def test_message_send_access_error():
    """
    A test for the message_send() function to check that an AccessError is
    thrown when a user tries to send a message to a channel they are not in.
    """
    workspace_reset()
    _, user1_token = user1()
    _, user2_token = user2()
    ch1, ch2 = chan1(user1_token), chan2(user2_token)
    ## user1 is in chan1 --> cannot send message in chan2
    with pytest.raises(AccessError):
        message_send(user1_token, ch2, "this is a valid message")
    ## user2 is in chan2 --> cannot send message in chan1
    with pytest.raises(AccessError):
        message_send(user2_token, ch1, "this is a valid message")


####################################################################
##                   Testing message_sendlater                    ##
####################################################################

def test_message_sendlater_valid():
    """
    A test for the message_sendlater() function under valid input.
    """
    workspace_reset()
    _, user1_token = user1()
    ch1 = chan1(user1_token)

    ## Send message and get message_id
    now = datetime.utcnow()
    time_now = int(now.replace(tzinfo=timezone.utc).timestamp())
    valid_message = message_sendlater(user1_token, ch1, "hello", time_now + 5)
    m_id = valid_message["message_id"]

    ## Check that the message has NOT been sent yet
    assert channel_messages(user1_token, ch1, 0)["messages"] == []

    ## Sleep for 5.5 seconds and check that the message has been sent
    time.sleep(5.5)
    assert channel_messages(user1_token, ch1, 0)["messages"][0]["message_id"] == m_id

def test_message_sendlater_input_errors():
    """
    A test for the message_sendlater() function under inputs that should
    throw InputErrors.
    """
    workspace_reset()

    ## Get a valid user and timestamp
    _, user1_token = user1()
    now = datetime.utcnow()
    time_now = int(now.replace(tzinfo=timezone.utc).timestamp())
    with pytest.raises(InputError):
        ## Assume channel_id of 1 does not exist
        message_sendlater(user1_token, 1, "hello", time_now + 5)

    ## Get a valid channel id and make a long message
    ch1 = chan1(user1_token)
    long_msg = "f" * 1001
    with pytest.raises(InputError):
        ## Message too long
        message_sendlater(user1_token, ch1, long_msg, time_now + 5)

    ## Check for messages sent in the past
    with pytest.raises(InputError):
        message_sendlater(user1_token, ch1, "hello", time_now - 5)

def test_message_sendlater_access_errors():
    """
    A test for the message_sendlater() function under inputs that should
    throw AccessErrors.
    """
    workspace_reset()
    ## Create two users and a channel for each
    _, user1_token = user1()
    _, user2_token = user2()
    ch1, ch2 = chan1(user1_token), chan2(user2_token)
    now = datetime.utcnow()
    time_now = int(now.replace(tzinfo=timezone.utc).timestamp())

    ## user1 cannot send messages in channel 2
    with pytest.raises(AccessError):
        message_sendlater(user1_token, ch2, "hello", time_now + 5)

    ## user2 cannot send messages in channel 1
    with pytest.raises(AccessError):
        message_sendlater(user2_token, ch1, "hello", time_now + 5)


####################################################################
##                     Testing message_react                      ##
####################################################################

def test_message_react_valid():
    """
    A test for the message_react() function under valid input.
    """
    workspace_reset()
    _, user1_token = user1()
    _, user2_token = user2()
    ch1 = chan1(user1_token)
    channel_join(user2_token, ch1)

    ## Send a message
    m_id = message_send(user1_token, ch1, "hello")["message_id"]

    ## Assert that there are no reacts yet
    assert channel_messages(user1_token, ch1, 0)["messages"][0]["reacts"] == []

    ## User1 reacts to the message
    message_react(user1_token, m_id, 1) ## 1 is the only valid react_id

    ## Assert that the react was successful
    assert channel_messages(user1_token, ch1, 0)["messages"][0]["reacts"] == [
        {
            "react_id": 1,
            "u_ids": [1],
            "is_this_user_reacted": True
        }
    ]

    ## What about when user2 makes the request?
    assert channel_messages(user2_token, ch1, 0)["messages"][0]["reacts"] == [
        {
            "react_id": 1,
            "u_ids": [1],
            "is_this_user_reacted": False
        }
    ]

    ## Let user2 react to the message
    message_react(user2_token, m_id, 1)
    assert channel_messages(user1_token, ch1, 0)["messages"][0]["reacts"] == [
        {
            "react_id": 1,
            "u_ids": [1, 2],
            "is_this_user_reacted": True
        }
    ]

    ## The result should be the same even if user2 made the request
    user1_req = channel_messages(user1_token, ch1, 0)["messages"][0]["reacts"]
    user2_req = channel_messages(user2_token, ch1, 0)["messages"][0]["reacts"]
    assert user1_req == user2_req

def test_message_react_input_errors():
    """
    A test for the message_react() function under inputs that should throw InputErrors.
    """
    workspace_reset()
    ## Create users, channels and messages
    _, user1_token = user1()
    _, user2_token = user2()
    ch1, ch2 = chan1(user1_token), chan2(user2_token)
    m1_id = message_send(user1_token, ch1, "hello")["message_id"]
    m2_id = message_send(user2_token, ch2, "hello2")["message_id"]

    ## Invalid react_id
    with pytest.raises(InputError):
        message_react(user1_token, m1_id, 99)

    ## Attempt to react to a message in another channel
    with pytest.raises(InputError):
        message_react(user1_token, m2_id, 1) ## 1 is a valid react_id

    ## React and attempt to react again
    message_react(user1_token, m1_id, 1)
    with pytest.raises(InputError):
        message_react(user1_token, m1_id, 1)


####################################################################
##                    Testing message_unreact                     ##
####################################################################

def test_message_unreact_valid():
    """
    A test for the message_unreact() function under valid input.
    """
    workspace_reset()
    _, user1_token = user1()
    _, user2_token = user2()
    ch1 = chan1(user1_token)
    channel_join(user2_token, ch1)

    ## Send a message
    m_id = message_send(user1_token, ch1, "hello")["message_id"]

    ## User1 and user2 react to the message
    message_react(user1_token, m_id, 1) ## 1 is the only valid react_id
    message_react(user2_token, m_id, 1)

    ## Assert that the reacts were successful
    assert channel_messages(user1_token, ch1, 0)["messages"][0]["reacts"] == [
        {
            "react_id": 1,
            "u_ids": [1, 2],
            "is_this_user_reacted": True
        }
    ]

    ## user2 unreacts
    message_unreact(user2_token, m_id, 1)

    ## Assert that the message no longer contains user2"s react
    assert channel_messages(user2_token, ch1, 0)["messages"][0]["reacts"] == [
        {
            "react_id": 1,
            "u_ids": [1],
            "is_this_user_reacted": False
        }
    ]
    assert channel_messages(user1_token, ch1, 0)["messages"][0]["reacts"] == [
        {
            "react_id": 1,
            "u_ids": [1],
            "is_this_user_reacted": True
        }
    ]

    ## user1 unreacts
    message_unreact(user1_token, m_id, 1)

    ## Assert that the message no longer contains user1"s react
    user1_req = channel_messages(user1_token, ch1, 0)["messages"][0]["reacts"]
    user2_req = channel_messages(user2_token, ch1, 0)["messages"][0]["reacts"]
    assert user1_req == []
    assert user1_req == user2_req

def test_message_unreact_input_errors():
    """
    A test for the message_unreact() function under inputs that should throw InputErrors.
    """
    workspace_reset()
    ## Create users, channels and messages
    _, user1_token = user1()
    _, user2_token = user2()
    ch1, ch2 = chan1(user1_token), chan2(user2_token)
    m1_id = message_send(user1_token, ch1, "hello")["message_id"]
    m2_id = message_send(user2_token, ch2, "hello2")["message_id"]

    ## Create react
    message_react(user1_token, m1_id, 1)

    ## Invalid react_id
    with pytest.raises(InputError):
        message_unreact(user1_token, m1_id, 99)

    ## Attempt to unreact to a message in another channel
    with pytest.raises(InputError):
        message_unreact(user1_token, m2_id, 1) ## 1 is a valid react_id

    ## Can only unreact if you have reacted
    with pytest.raises(InputError):
        message_unreact(user2_token, m2_id, 1)


####################################################################
##                      Testing message_pin                       ##
####################################################################

def test_message_pin_valid():
    """
    A test for the message_pin() function under valid input.
    """
    workspace_reset()
    _, user1_token = user1()
    _, user2_token = user2()
    ch1 = chan1(user1_token)
    channel_join(user2_token, ch1)

    ## user1 sends message
    m_id = message_send(user1_token, ch1, "important message")["message_id"]

    ## Check the message isn"t pinned
    user1_pin = channel_messages(user1_token, ch1, 0)["messages"][0]["is_pinned"]
    user2_pin = channel_messages(user2_token, ch1, 0)["messages"][0]["is_pinned"]
    assert not user1_pin
    assert not user2_pin

    ## Pin the message
    message_pin(user1_token, m_id)

    ## Check that it is indeed pinned
    user1_pin = channel_messages(user1_token, ch1, 0)["messages"][0]["is_pinned"]
    user2_pin = channel_messages(user2_token, ch1, 0)["messages"][0]["is_pinned"]
    assert user1_pin
    assert user2_pin

def test_message_pin_input_errors():
    """
    A test for the message_pin() function under inputs that should throw InputErrors.
    """
    workspace_reset()
    _, user1_token = user1()
    ch1 = chan1(user1_token)

    ## Message does not exist
    with pytest.raises(InputError):
        message_pin(user1_token, 1)

    ## User1 sends a message
    m_id = message_send(user1_token, ch1, "important message")["message_id"]

    ## Pin the message and attempt to pin it again
    message_pin(user1_token, m_id)
    with pytest.raises(InputError):
        message_pin(user1_token, m_id)

def test_message_pin_access_errors():
    """
    A test for the message_pin() function under inputs that should throw AccessErrors.
    """
    workspace_reset()
    _, user1_token = user1()
    _, user2_token = user2()
    ch1 = chan1(user1_token)
    m_id = message_send(user1_token, ch1, "message")["message_id"]

    ## User2 is not in chan1 so cannot pin a message in chan1
    with pytest.raises(AccessError):
        message_pin(user2_token, m_id)

    channel_join(user2_token, ch1)
    ## User2 is not an owner so cannot pin
    with pytest.raises(AccessError):
        message_pin(user2_token, m_id)


####################################################################
##                      Testing message_unpin                     ##
####################################################################

def test_message_unpin_valid():
    """
    A test for the message_unpin() function under valid input.
    """
    workspace_reset()
    _, user1_token = user1()
    _, user2_token = user2()
    ch1 = chan1(user1_token)
    channel_join(user2_token, ch1)

    ## user1 sends message
    m_id = message_send(user1_token, ch1, "important message")["message_id"]

    ## Pin the message
    message_pin(user1_token, m_id)

    ## Check that it is indeed pinned
    user1_pin = channel_messages(user1_token, ch1, 0)["messages"][0]["is_pinned"]
    user2_pin = channel_messages(user2_token, ch1, 0)["messages"][0]["is_pinned"]
    assert user1_pin
    assert user2_pin

    ## Unpin the message
    message_unpin(user1_token, m_id)

    ## Check that the message is no longer pinned
    user1_pin = channel_messages(user1_token, ch1, 0)["messages"][0]["is_pinned"]
    user2_pin = channel_messages(user2_token, ch1, 0)["messages"][0]["is_pinned"]
    assert not user1_pin
    assert not user2_pin

def test_message_unpin_input_errors():
    """
    A test for the message_unpin() function under inputs that should throw InputErrors.
    """
    workspace_reset()
    _, user1_token = user1()
    ch1 = chan1(user1_token)

    ## Message does not exist
    with pytest.raises(InputError):
        message_unpin(user1_token, 1)

    ## User1 sends a message and pins it
    m_id = message_send(user1_token, ch1, "important message")["message_id"]
    message_pin(user1_token, m_id)

    ## Unpin the message and attempt to unpin it again
    message_unpin(user1_token, m_id)
    with pytest.raises(InputError):
        message_unpin(user1_token, m_id)

def test_message_unpin_access_errors():
    """
    A test for the message_unpin() function under inputs that should throw AccessErrors.
    """
    workspace_reset()
    _, user1_token = user1()
    _, user2_token = user2()
    ch1 = chan1(user1_token)
    m_id = message_send(user1_token, ch1, "message")["message_id"]

    ## User2 is not in chan1 so cannot unpin a message in chan1
    message_pin(user1_token, m_id)
    with pytest.raises(AccessError):
        message_unpin(user2_token, m_id)

    channel_join(user2_token, ch1)
    ## User2 is not an owner so cannot unpin
    with pytest.raises(AccessError):
        message_unpin(user2_token, m_id)


####################################################################
##                    Testing message_remove                      ##
####################################################################

def test_message_remove_valid_input():
    """
    A test for the message_remove() function under VALID input.
    """
    workspace_reset()
    user1_id, user1_token = user1()
    ch1 = chan1(user1_token)
    ## user1 sends a message
    msg = message_send(user1_token, ch1, "This message will be deleted")
    ## Assume channel_messages() works and check if message was sent
    corr_m = channel_messages(user1_token, ch1, 0)["messages"][0]
    assert corr_m["message_id"] == msg["message_id"]
    assert corr_m["u_id"] == user1_id
    assert corr_m["message"] == "This message will be deleted"

    ## Remove the message
    message_remove(user1_token, msg["message_id"])
    ## Check that the message was removed
    assert channel_messages(user1_token, ch1, 0)["messages"] == []

def test_message_remove_input_error():
    """
    A test for the message_remove() function to check that an InputError
    will be raised when a message_id no longer exists.
    """
    workspace_reset()
    _, user1_token = user1()
    ch1 = chan1(user1_token)
    ## Send a message, store its ID and then delete the message
    msg = message_send(user1_token, ch1, "This message will be deleted")
    m_id = msg["message_id"]
    message_remove(user1_token, m_id)
    with pytest.raises(InputError):
        ## Delete the message again but it should fail as its already deleted
        message_remove(user1_token, m_id)

def test_message_remove_access_error():
    """
    A test for the message_remove() function to check that an AccessError
    is raised when a user tries to delete another user"s message AND is not
    an admin or owner of the channel.
    """
    workspace_reset()
    _, user1_token = user1()
    _, user2_token = user2()
    ch1 = chan1(user1_token) ## user1 is the only admin of chan1
    ## Since ch1 is public, assume channel_join() works and have user2 join
    channel_join(user2_token, ch1) ## user2 is not an admin of this channel
    ## user1 sends a message
    msg = message_send(user1_token, ch1, "Do not delete my message")
    ## user2 tries to DELETE user1"s message but is not an admin so an
    ## AccessError should be raised
    with pytest.raises(AccessError):
        message_remove(user2_token, msg["message_id"])


####################################################################
##                      Testing message_edit                      ##
####################################################################

def test_message_edit_valid_input():
    """
    A test for the message_edit() function under VALID input.
    """
    workspace_reset()
    user1_id, user1_token = user1()
    ch1 = chan1(user1_token)
    msg = message_send(user1_token, ch1, "This message will be edited")
    ## Check that the message has sent
    corr_m = channel_messages(user1_token, ch1, 0)["messages"][0]
    assert corr_m["message_id"] == msg["message_id"]
    assert corr_m["u_id"] == user1_id
    assert corr_m["message"] == "This message will be edited"
    message_edit(user1_token, msg["message_id"], "Edited")
    ## Check that the message has indeed been EDITED
    new_m = channel_messages(user1_token, ch1, 0)["messages"][0]
    assert new_m["message"] == "Edited"

def test_message_edit_empty_string():
    """
    A test for the message_edit() function that checks that if the edited
    message is an empty string, then the message should be deleted.
    """
    workspace_reset()
    user1_id, user1_token = user1()
    ch1 = chan1(user1_token)
    msg = message_send(user1_token, ch1, "This message will be edited & deleted")
    ## Check that the message has sent
    corr_m = channel_messages(user1_token, ch1, 0)["messages"][0]
    assert corr_m["message_id"] == msg["message_id"]
    assert corr_m["u_id"] == user1_id
    assert corr_m["message"] == "This message will be edited & deleted"
    message_edit(user1_token, msg["message_id"], "") ## empty string
    ## Check that the message has indeed been DELETED
    assert channel_messages(user1_token, ch1, 0)["messages"] == []

def test_message_edit_access_error():
    """
    A test for the message_edit() function that checks if an AccessError
    is raised when a user is trying to edit another users message AND
    is not an admin of the channel.
    """
    workspace_reset()
    _, user1_token = user1()
    _, user2_token = user2()
    ch1 = chan1(user1_token) ## user1 is the only admin of chan1
    ## Since ch1 is public, assume channel_join() works and have user2 join
    channel_join(user2_token, ch1) ## user2 is not an admin of this channel
    ## user1 sends a message
    msg = message_send(user1_token, ch1, "Do not edit my message")
    ## user2 tries to EDIT user1"s message but is not an admin so an
    ## AccessError should be raised
    with pytest.raises(AccessError):
        message_edit(user2_token, msg["message_id"], "I cannot edit")


####################################################################
##                       Other AccessErrors                       ##
####################################################################

def test_message_access_error():
    """
    A test for all message.py functions that check that an AccessError is
    thrown when passed in an invalid token.
    """
    workspace_reset()
    _, user1_token = user1()
    ch1 = chan1(user1_token)
    m_id = message_send(user1_token, ch1, "Hello world")["message_id"]
    ## Add 50 "a"s onto the end of user1_token to produce an invalid token
    ##
    ## This token is assumed to be invalid since there are no other registered
    ## users for this token to belong to
    invalid_token = user1_token + ("a" * 50)
    with pytest.raises(AccessError):
        message_send(invalid_token, ch1, "Hello world")
    now = datetime.utcnow()
    time_now = int(now.replace(tzinfo=timezone.utc).timestamp())
    with pytest.raises(AccessError):
        message_sendlater(invalid_token, ch1, m_id, time_now + 5)
    with pytest.raises(AccessError):
        message_react(invalid_token, m_id, 1)
    message_react(user1_token, m_id, 1)
    with pytest.raises(AccessError):
        message_unreact(invalid_token, m_id, 1)
    with pytest.raises(AccessError):
        message_pin(invalid_token, m_id)
    message_pin(user1_token, m_id)
    with pytest.raises(AccessError):
        message_unpin(invalid_token, m_id)
    with pytest.raises(AccessError):
        message_remove(invalid_token, m_id)
    with pytest.raises(AccessError):
        message_edit(invalid_token, m_id, "Hello guys")
