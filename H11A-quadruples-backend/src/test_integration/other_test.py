"""
Integration tests for the functions implemented in other.py.
H11A-quadruples, April 2020.
"""

from datetime import datetime, timezone
import time
import pytest
from error import InputError, AccessError
from funcs.channels import channels_listall
from funcs.other import (
    users_all,
    search,
    standup_start,
    standup_active,
    standup_send,
    admin_userpermission_change,
    admin_user_remove,
    workspace_reset
)
from funcs.user import (
    user_profile_setname,
    user_profile_setemail,
    user_profile_sethandle
)
from funcs.channel import channel_messages, channel_leave, channel_join, channel_details
from funcs.message import message_send, message_remove, message_edit
from helpers.registers import user1, user2, user3, chan1, chan2, chan3
from port_settings import BASE_URL

####################################################################
##                        Testing users_all                       ##
####################################################################

def test_users_all_one():
    """
    A test for the users_all() function under a VALID input of one user.
    """
    workspace_reset()
    user1_id, user1_token = user1()
    ## Test if users_all() returns the correct dictionary for user1
    ## Should return a dictionary containing a list containing a dictionary
    assert users_all(user1_token) == {
        "users": [
            {
                "u_id": user1_id,
                "email": "bob.ross@unsw.edu.au",
                "name_first": "Bob",
                "name_last": "Ross",
                "handle_str": "bobross",
                "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
            }
        ]
    }

def test_users_all_two():
    """
    A test for the users_all() function under a VALID input of two users.
    """
    workspace_reset()
    user1_id, user1_token = user1()
    user2_id, user2_token = user2()
    ## Test if users_all() returns the correct dictionary for users 1 & 2
    ## Should return a dictionary containing a list containing dictionaries
    assert users_all(user1_token) == {
        "users": [
            {
                "u_id": user1_id,
                "email": "bob.ross@unsw.edu.au",
                "name_first": "Bob",
                "name_last": "Ross",
                "handle_str": "bobross",
                "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
            },
            {
                "u_id": user2_id,
                "email": "elon.musk@unsw.edu.au",
                "name_first": "Elon",
                "name_last": "Musk",
                "handle_str": "elonmusk",
                "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
            }
        ]
    }
    ## The user list should be the same regardless of who makes the request
    assert users_all(user1_token) == users_all(user2_token)

def test_users_all_other():
    """
    A test for the users_all() function under a VALID input of three users.
    Also calls a variety of user functions to test if users_all() updates
    whenever a user updates their information.
    """
    workspace_reset()
    user1_id, user1_token = user1()
    user2_id, user2_token = user2()
    user3_id, user3_token = user3()
    ## Test if users_all() returns the correct dictionary BEFORE calling
    ## any user_profile functions
    assert users_all(user1_token) == {
        "users": [
            {
                "u_id": user1_id,
                "email": "bob.ross@unsw.edu.au",
                "name_first": "Bob",
                "name_last": "Ross",
                "handle_str": "bobross",
                "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
            },
            {
                "u_id": user2_id,
                "email": "elon.musk@unsw.edu.au",
                "name_first": "Elon",
                "name_last": "Musk",
                "handle_str": "elonmusk",
                "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
            },
            {
                "u_id": user3_id,
                "email": "steve.jobs@unsw.edu.au",
                "name_first": "Steve",
                "name_last": "Jobs",
                "handle_str": "stevejobs",
                "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
            }
        ]
    }
    ## Again, the user list should be the same regardless of who
    ## makes the request
    assert users_all(user1_token) == users_all(user2_token)
    assert users_all(user2_token) == users_all(user3_token)

    ## The following assumes user_profile_setname(), user_profile_setemail(),
    ## and user_profile_sethandle() are all functional
    user_profile_setname(user1_token, "Ross", "Bob")
    user_profile_setemail(user2_token, "elon.musk@gmail.com")
    user_profile_sethandle(user3_token, "jobssteve")
    ## Test if users_all() updates with these changes just made
    assert users_all(user1_token) == {
        "users": [
            {
                "u_id": user1_id,
                "email": "bob.ross@unsw.edu.au",
                "name_first": "Ross",
                "name_last": "Bob",
                "handle_str": "bobross",
                "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
            },
            {
                "u_id": user2_id,
                "email": "elon.musk@gmail.com",
                "name_first": "Elon",
                "name_last": "Musk",
                "handle_str": "elonmusk",
                "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
            },
            {
                "u_id": user3_id,
                "email": "steve.jobs@unsw.edu.au",
                "name_first": "Steve",
                "name_last": "Jobs",
                "handle_str": "jobssteve",
                "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
            }
        ]
    }


####################################################################
##                         Testing search                         ##
####################################################################

#------------------------#
#       ASSUMPTIONS      #
#------------------------#

# >> if query_str is a SUBSET of a message, that message will be shown
# >> query_str is not case sensitive
#        >> ie. search for "HELLO" == search for "hello"
#        >> this is for functionality purposes (easier to find messages)

#------------------------#
#         HELPER         #
#------------------------#

def messages(user1_token, user2_token, user3_token, ch1, ch2, ch3):
    """
    Each user sends two messages each to the channel they own.

    Args:
        param1: Token for user1.
        user2_token (str): Token for user2.
        user3_token (str): Token for user3.
        ch1 (int): channel_id for the first channel.
        ch2 (int): channel_id for the second channel.
        ch3 (int): channel_id for the third channel.
    Returns:
        A 6-tuple containing the message_id (int) of all 6 messages.
    """
    ## Assume message_send() works
    message1 = message_send(user1_token, ch1, "user1 chan1 message1")
    message2 = message_send(user1_token, ch1, "user1 chan1 message2")
    message3 = message_send(user2_token, ch2, "user2 chan2 message1")
    message4 = message_send(user2_token, ch2, "user2 chan2 message2")
    message5 = message_send(user3_token, ch3, "user3 chan3 message1")
    message6 = message_send(user3_token, ch3, "user3 chan3 message2")
    return (
        message1["message_id"],
        message2["message_id"],
        message3["message_id"],
        message4["message_id"],
        message5["message_id"],
        message6["message_id"]
    )

#------------------------#
#        TESTING         #
#------------------------#

def test_search_no_overlap():
    """
    A test for the search() function where each user is in one different
    channel each.
    """
    workspace_reset()
    user1_id, user1_token = user1()
    user2_id, user2_token = user2()
    user3_id, user3_token = user3()
    ch1, ch2, ch3 = chan1(user1_token), chan2(user2_token), chan3(user3_token)
    msg1, msg2, msg3, msg4, msg5, msg6 = messages(
        user1_token, user2_token, user3_token,
        ch1, ch2, ch3
    )
    ## Check that user1"s searches succeed
    assert len(search(user1_token, "user1")["messages"]) == 2
    message1 = search(user1_token, "user1")["messages"][0] ## assume index 0
    message2 = search(user1_token, "user1")["messages"][1] ## assume index 1
    assert message1["message_id"] == msg2
    assert message1["u_id"] == user1_id
    assert message1["message"] == "user1 chan1 message2"
    assert message2["message_id"] == msg1
    assert message2["u_id"] == user1_id
    assert message2["message"] == "user1 chan1 message1"

    ## user1"s search for "message1" should only return message 1
    assert len(search(user1_token, "message1")["messages"]) == 1
    message3 = search(user1_token, "message1")["messages"][0]
    assert message3["message_id"] == msg1
    assert message3["u_id"] == user1_id
    assert message3["message"] == "user1 chan1 message1"

    ## Check that user2"s searches succeed
    assert len(search(user2_token, "user2")["messages"]) == 2
    message4 = search(user2_token, "user2")["messages"][0] ## assume index 0
    message5 = search(user2_token, "user2")["messages"][1] ## assume index 1
    assert message4["message_id"] == msg4
    assert message4["u_id"] == user2_id
    assert message4["message"] == "user2 chan2 message2"
    assert message5["message_id"] == msg3
    assert message5["u_id"] == user2_id
    assert message5["message"] == "user2 chan2 message1"

    ## Check that user3"s searches succeed
    assert len(search(user3_token, "user3")["messages"]) == 2
    message6 = search(user3_token, "user3")["messages"][0] ## assume index 0
    message7 = search(user3_token, "user3")["messages"][1] ## assume index 1
    assert message6["message_id"] == msg6
    assert message6["u_id"] == user3_id
    assert message6["message"] == "user3 chan3 message2"
    assert message7["message_id"] == msg5
    assert message7["u_id"] == user3_id
    assert message7["message"] == "user3 chan3 message1"

## BEFORE:    user1 is in chan1
##            user1 makes a search
## DURING:    user1 joins chan2
## AFTER:     user1 makes a search      (same search)
##            user1 search results should change
## EXTRA:     user1 leaves chan2
def test_search_overlap():
    """
    A test for the search() function where two users are in the same channel.
    """
    workspace_reset()
    user1_id, user1_token = user1()
    user2_id, user2_token = user2()
    _, user3_token = user3()
    ch1, ch2, ch3 = chan1(user1_token), chan2(user2_token), chan3(user3_token)
    msg1, _, msg3, _, _, _ = messages(
        user1_token, user2_token, user3_token,
        ch1, ch2, ch3
    )
    ## user1 makes a search (BEFORE joining chan2)
    assert len(search(user1_token, "message1")["messages"]) == 1
    message1 = search(user1_token, "message1")["messages"][0]
    assert message1["message_id"] == msg1
    assert message1["u_id"] == user1_id
    assert message1["message"] == "user1 chan1 message1"

    ## user1 joins chan2 (a PUBLIC channel)
    ## Assume channel_join() works
    channel_join(user1_token, ch2)

    ## Check that search() has been updated
    assert len(search(user1_token, "message1")["messages"]) == 2
    message2 = search(user1_token, "message1")["messages"][0] ## assume index 0
    message3 = search(user1_token, "message1")["messages"][1] ## assume index 1
    assert message2["message_id"] == msg3
    assert message2["u_id"] == user2_id
    assert message2["message"] == "user2 chan2 message1"
    assert message3["message_id"] == msg1
    assert message3["u_id"] == user1_id
    assert message3["message"] == "user1 chan1 message1"

    ## user1 leaves chan2
    ## Assume channel_leave() works
    channel_leave(user1_token, ch2)

    ## Check that search() has been updated
    assert len(search(user1_token, "message1")["messages"]) == 1
    message4 = search(user1_token, "message1")["messages"][0]
    assert message4["message_id"] == msg1
    assert message4["u_id"] == user1_id
    assert message4["message"] == "user1 chan1 message1"

## search for "HELLO" should be equal to search for "hello"
## For functionality purposes (mirrors functionality of CTRL+F of web browsers)
def test_search_case_sensitive():
    """
    A test for the search() function to validate the assumption made that
    query_str should not be case sensitive.
    """
    workspace_reset()
    _, user1_token = user1()
    _, user2_token = user2()
    _, user3_token = user3()
    ch1, ch2, ch3 = chan1(user1_token), chan2(user2_token), chan3(user3_token)
    messages(
        user1_token, user2_token, user3_token,
        ch1, ch2, ch3
    )
    assert search(user1_token, "USER1") == search(user1_token, "user1")
    assert search(user1_token, "CHAN1") == search(user1_token, "chan1")
    assert search(user2_token, "USER2") == search(user2_token, "user2")
    assert search(user2_token, "CHAN2") == search(user2_token, "chan2")
    assert search(user3_token, "USER3") == search(user3_token, "user3")
    assert search(user3_token, "CHAN3") == search(user3_token, "chan3")

## BEFORE:    user1 makes a search
## DURING:    user1 removes a message (one that contains the query_str)
## AFTER:     user1 makes a search    (using the same query_str)
##            user1 search results should change
def test_search_remove():
    """
    A test for the search() function where a user removes a message containing
    their query_str and hence should be removed from the search results.
    """
    workspace_reset()
    user1_id, user1_token = user1()
    _, user2_token = user2()
    _, user3_token = user3()
    ch1, ch2, ch3 = chan1(user1_token), chan2(user2_token), chan3(user3_token)
    msg1, msg2, _, _, _, _ = messages(
        user1_token, user2_token, user3_token,
        ch1, ch2, ch3
    )
    ## user1 makes a search (BEFORE removing message2)
    assert len(search(user1_token, "message")["messages"]) == 2
    message1 = search(user1_token, "message")["messages"][0] ## assume index 0
    message2 = search(user1_token, "message")["messages"][1] ## assume index 1
    assert message1["message_id"] == msg2
    assert message1["u_id"] == user1_id
    assert message1["message"] == "user1 chan1 message2"
    assert message2["message_id"] == msg1
    assert message2["u_id"] == user1_id
    assert message2["message"] == "user1 chan1 message1"

    ## user1 removes message2
    ## Assume message_remove() works
    message_remove(user1_token, msg2)

    ## Check that search() has been updated
    assert len(search(user1_token, "message")["messages"]) == 1
    message3 = search(user1_token, "message")["messages"][0]
    assert message3["message_id"] == msg1
    assert message3["u_id"] == user1_id
    assert message3["message"] == "user1 chan1 message1"

    ## user1 removes message1
    message_remove(user1_token, msg1)
    ## Check that the search() has been updated
    assert search(user1_token, "message") == {"messages": []}

## BEFORE:    user1 makes a search
## DURING:    user1 edit a message    (so that message does not have query_str)
## AFTER:     user1 makes a search    (using the same query_str)
##            user1 search results should change
def test_search_edit():
    """
    A test for the search() function where a user edits a message containing
    their query_str so that it is removed from the search results.
    """
    workspace_reset()
    user1_id, user1_token = user1()
    _, user2_token = user2()
    _, user3_token = user3()
    ch1, ch2, ch3 = chan1(user1_token), chan2(user2_token), chan3(user3_token)
    msg1, msg2, _, _, _, _ = messages(
        user1_token, user2_token, user3_token,
        ch1, ch2, ch3
    )
    ## user1 makes a search (BEFORE editing message2)
    assert len(search(user1_token, "message")["messages"]) == 2
    message1 = search(user1_token, "message")["messages"][0] ## assume index 0
    message2 = search(user1_token, "message")["messages"][1] ## assume index 1
    assert message1["message_id"] == msg2
    assert message1["u_id"] == user1_id
    assert message1["message"] == "user1 chan1 message2"
    assert message2["message_id"] == msg1
    assert message2["u_id"] == user1_id
    assert message2["message"] == "user1 chan1 message1"

    ## user1 edits message2
    ## Assume message_edit() works
    message_edit(user1_token, msg2, "bye bye")

    ## Check that search() has been updated
    assert len(search(user1_token, "message")["messages"]) == 1
    message3 = search(user1_token, "message")["messages"][0]
    assert message3["message_id"] == msg1
    assert message3["u_id"] == user1_id
    assert message3["message"] == "user1 chan1 message1"

    ## user1 re-edits message2
    message_edit(user1_token, msg2, "message re-edit")

    ## Check that the search() has been updated
    assert len(search(user1_token, "message")["messages"]) == 2
    message4 = search(user1_token, "message")["messages"][0] ## assume index 0
    message5 = search(user1_token, "message")["messages"][1] ## assume index 1
    assert message4["message_id"] == msg2
    assert message4["u_id"] == user1_id
    assert message4["message"] == "message re-edit"
    assert message5["message_id"] == msg1
    assert message5["u_id"] == user1_id
    assert message5["message"] == "user1 chan1 message1"

def test_search_empty():
    """
    A test for the search() function where query_str has no matches.
    """
    workspace_reset()
    _, user1_token = user1()
    _, user2_token = user2()
    _, user3_token = user3()
    ch1, ch2, ch3 = chan1(user1_token), chan2(user2_token), chan3(user3_token)
    messages(
        user1_token, user2_token, user3_token,
        ch1, ch2, ch3
    )
    ## If user1 searches for a query_str "user2" then return an empty list
    assert search(user1_token, "user2") == {"messages": []}
    ## Similarly:
    assert search(user1_token, "user3") == {"messages": []}
    assert search(user2_token, "user1") == {"messages": []}
    assert search(user2_token, "user3") == {"messages": []}
    assert search(user3_token, "user1") == {"messages": []}
    assert search(user3_token, "user2") == {"messages": []}


####################################################################
##                   Testing standup functions                    ##
####################################################################

def test_standup_valid():
    """
    A test for the standup functions under valid inputs.
    """
    workspace_reset()
    user1_id, user1_token = user1()
    _, user2_token = user2()
    _, user3_token = user3()
    ch1 = chan1(user1_token)
    channel_join(user2_token, ch1)
    channel_join(user3_token, ch1)

    ## Assert standup_active is false
    assert standup_active(user1_token, ch1) == {
        "is_active": False,
        "time_finish": None
    }

    ## Find the time_now and start the standup
    now = datetime.utcnow()
    time_now = int(now.replace(tzinfo=timezone.utc).timestamp())
    time_finish = standup_start(user1_token, ch1, 10)["time_finish"]
    assert time_finish == time_now + 10

    ## Assert standup_active is true
    assert standup_active(user1_token, ch1) == {
        "is_active": True,
        "time_finish": time_now + 10
    }

    ## Send some messages in the standup
    standup_send(user1_token, ch1, "user1 msg1")
    standup_send(user1_token, ch1, "user1 msg2")
    standup_send(user2_token, ch1, "user2 msg1")
    time.sleep(5)
    standup_send(user2_token, ch1, "user2 msg2")
    standup_send(user3_token, ch1, "user3 msg1")

    ## Check channel_messages before standup finishes
    assert channel_messages(user1_token, ch1, 0)["messages"] == []
    time.sleep(5)

    ## Check channel_messages
    expected_msg = """bob: user1 msg1\n\
bob: user1 msg2\n\
elon: user2 msg1\n\
elon: user2 msg2\n\
steve: user3 msg1\n"""
    assert channel_messages(user1_token, ch1, 0) == {
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
    A test for the standup_start() function under invalid inputs.
    """
    workspace_reset()
    _, user1_token = user1()

    ## Channel does not exist
    with pytest.raises(InputError):
        standup_start(user1_token, 1, 10)

    ## Begin a standup and attempt to start another one
    ch1 = chan1(user1_token)
    standup_start(user1_token, ch1, 0.5)
    with pytest.raises(InputError):
        standup_start(user1_token, ch1, 0.5)

def test_standup_active_invalid():
    """
    A test for the standup_active() function under invalid inputs.
    """
    workspace_reset()
    _, user1_token = user1()

    ## Channel does not exist
    with pytest.raises(InputError):
        standup_active(user1_token, 1) ## 1 isn"t a valid id

def test_standup_send_invalid():
    """
    A test for the standup_send() function under invalid inputs.
    """
    workspace_reset()
    _, user1_token = user1()
    _, user2_token = user2()

    ## Channel does not exist
    with pytest.raises(InputError):
        standup_send(user1_token, 1, "hello")

    ## Create the channel
    ch1 = chan1(user1_token)

    ## An active standup is not currently running
    with pytest.raises(InputError):
        standup_send(user1_token, ch1, "hello")

    ## User2 is not a member of chan1
    standup_start(user1_token, ch1, 1) ## start a standup
    with pytest.raises(AccessError):
        standup_send(user2_token, ch1, "hello")

    ## Message too long
    long_msg = "f" * 1001
    with pytest.raises(InputError):
        standup_send(user1_token, ch1, long_msg)


####################################################################
##               Testing admin_userpermission_change              ##
####################################################################

def test_admin_userpermission_change_valid():
    """
    A test for the admin_userpermission_change() function under valid inputs.
    """
    workspace_reset()
    user1_id, user1_token = user1()
    user2_id, user2_token = user2()
    ch1, ch2 = chan1(user1_token), chan2(user2_token)

    ## Set user2 to be a Slackr owner
    admin_userpermission_change(user1_token, user2_id, 1)

    ## user2 joins chan1 and should be an owner
    channel_join(user2_token, ch1)
    assert channel_details(user2_token, ch1)["owner_members"] == [
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

    ## Set user1 to be a Slackr member
    admin_userpermission_change(user2_token, user1_id, 2)

    ## user1 joins chan2 and should NOT be an owner
    channel_join(user1_token, ch2)
    assert channel_details(user1_token, ch2)["owner_members"] == [
        {
            "u_id": user2_id,
            "name_first": "Elon",
            "name_last": "Musk",
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        }
    ]

def test_admin_userpermission_change_invalid():
    """
    A test for the admin_userpermission_change() function under invalid inputs.
    """
    workspace_reset()
    user1_id, user1_token = user1()

    ## User2 does not exist
    with pytest.raises(InputError):
        admin_userpermission_change(user1_token, 99, 1)
        ## Assumed 99 is a not a valid user

    ## Invalid permission_id
    user2_id, user2_token = user2()
    with pytest.raises(InputError):
        admin_userpermission_change(user1_token, user2_id, 99)
        ## 99 is not a valid permission_id

    ## User2 is not a Slackr owner and is therefore not authorised
    with pytest.raises(AccessError):
        admin_userpermission_change(user2_token, user1_id, 2)


####################################################################
##                     Testing admin_user_remove                  ##
####################################################################

def test_admin_user_remove_valid():
    """
    A test for the admin_user_remove() function under valid inputs.
    """
    workspace_reset()
    _, user1_token = user1()
    user2_id, _ = user2()

    ## Delete user2 from Slackr
    admin_user_remove(user1_token, user2_id)

    ## Check that user2 has been deleted
    all_users = users_all(user1_token)["users"]
    assert all(user["u_id"] != user2_id for user in all_users)

def test_admin_user_remove_invalid_input():
    """
    A test for the admin_user_remove() function under invalid inputs.
    """
    workspace_reset()
    user1_id, user1_token = user1()
    _, user2_token = user2()

    ## Delete user with invalid user_id
    with pytest.raises(InputError):
        admin_user_remove(user1_token, -9999)

    ## Deleting a user but not an admin
    with pytest.raises(AccessError):
        admin_user_remove(user2_token, user1_id)


####################################################################
##                     Testing workspace_reset                    ##
####################################################################

def test_workspace_reset():
    """
    A test for the workspace_reset() function.
    """
    workspace_reset()
    ## Register some users
    _, user1_token = user1()
    _, user2_token = user2()
    _, user3_token = user3()

    ## Create some channels
    ch1, ch2, ch3 = chan1(user1_token), chan2(user2_token), chan3(user3_token)

    ## Send some messages
    messages(
        user1_token, user2_token, user3_token,
        ch1, ch2, ch3
    )

    ## Reset the workspace
    workspace_reset()

    ## Assert that there are no more users, channels and messages
    with pytest.raises(AccessError):
        users_all(user1_token) ## token should not exist anymore
    with pytest.raises(AccessError):
        channels_listall(user1_token)
    with pytest.raises(AccessError):
        channel_messages(user1_token, ch1, 0)


####################################################################
##                       Other AccessErrors                       ##
####################################################################

def test_other_access_error():
    """
    A test for all other.py functions that check that an AccessError is
    thrown when passed in an invalid token.
    """
    workspace_reset()
    _, user1_token = user1()
    ## Add 50 "a"s onto the end of user1_token to produce an invalid token
    ##
    ## This token is assumed to be invalid since there are no other registered
    ## users for this token to belong to
    invalid_token = user1_token + ("a" * 50)
    with pytest.raises(AccessError):
        users_all(invalid_token)
    with pytest.raises(AccessError):
        search(invalid_token, "message")
    ch1 = chan1(user1_token)
    with pytest.raises(AccessError):
        standup_start(invalid_token, ch1, 1)
    with pytest.raises(AccessError):
        standup_active(invalid_token, ch1)
    standup_start(user1_token, ch1, 0.5)
    with pytest.raises(AccessError):
        standup_send(invalid_token, ch1, "message")
    user2_id, _ = user2()
    with pytest.raises(AccessError):
        admin_userpermission_change(invalid_token, user2_id, 1)
    with pytest.raises(AccessError):
        admin_user_remove(invalid_token, user2_id)
