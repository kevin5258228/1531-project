"""
Integration tests for the functions implemented in channels.py.
H11A-quadruples, April 2020.
"""

import pytest
from error import InputError, AccessError
from funcs.channels import channels_list, channels_listall, channels_create
from funcs.channel import channel_join, channel_leave
from funcs.other import workspace_reset
from helpers.registers import user1, user2

####################################################################
##                       Helper functions                         ##
####################################################################

def chan1(user1_token):
    """
    Create a public channel "general_bob" belonging to user1.

    Args:
        user1_token (str): Token for user1.
    Returns:
        channel_id (int) of newly created channel.
    """
    ## Assume channels_create() works
    channel = channels_create(user1_token, "general_bob", True)
    return channel["channel_id"]

def chan2(user1_token):
    """
    Create a public channel "random_bob" belonging to user1.

    Args:
        user1_token (str): Token for user1.
    Returns:
        channel_id (int) of newly created channel.
    """
    channel = channels_create(user1_token, "random_bob", True)
    return channel["channel_id"]

def chan3(user2_token):
    """
    Create a public channel "general_elon" belonging to user2.

    Args:
        user2_token (str): Token for user2.
    Returns:
        channel_id (int) of newly created channel.
    """
    channel = channels_create(user2_token, "general_elon", True)
    return channel["channel_id"]

def chan4(user2_token):
    """
    Create a public channel "random_elon" belonging to user2.

    Args:
        user2_token (str): Token for user2.
    Returns:
        channel_id (int) of newly created channel.
    """
    channel = channels_create(user2_token, "random_elon", True)
    return channel["channel_id"]

## BOB'S CHANNELS: chan1, chan2
## ELON'S CHANNELS: chan3, chan4


####################################################################
##                     Testing channels_list                      ##
####################################################################

def test_channels_list_one_user():
    """
    A test for the channels_list() function for ONE user who has joined
    two channels.
    """
    workspace_reset()
    _, user1_token = user1()
    ch1, ch2 = chan1(user1_token), chan2(user1_token)
    assert channels_list(user1_token) == {
        "channels": [
            {
                "channel_id": ch1,
                "name": "general_bob"
            },
            {
                "channel_id": ch2,
                "name": "random_bob"
            }
        ]
    }

def test_channels_list_two_users():
    """
    A test for the channels_list() function for TWO users who have joined
    two channels each (a total of 4 channels).
    """
    workspace_reset()
    _, user1_token = user1()
    _, user2_token = user2()
    ch1, ch2 = chan1(user1_token), chan2(user1_token)
    ch3, ch4 = chan3(user2_token), chan4(user2_token)
    ## Test that user1 is a part of chan1 and chan2 only
    assert channels_list(user1_token) == {
        "channels": [
            {
                "channel_id": ch1,
                "name": "general_bob"
            },
            {
                "channel_id": ch2,
                "name": "random_bob"
            }
        ]
    }
    ## Test that user2 is a part of chan3 and chan4 only
    assert channels_list(user2_token) == {
        "channels": [
            {
                "channel_id": ch3,
                "name": "general_elon"
            },
            {
                "channel_id": ch4,
                "name": "random_elon"
            }
        ]
    }

def test_channels_list_join():
    """
    A test for the channels_list() function for TWO users who have joined
    a common channel between them.
    """
    workspace_reset()
    _, user1_token = user1()
    _, user2_token = user2()
    ch1, ch2 = chan1(user1_token), chan2(user1_token)
    ch3 = chan3(user2_token)

    ## Test that user2 is a part of chan3 BEFORE joining chan2
    assert channels_list(user2_token) == {
        "channels": [
            {
                "channel_id": ch3,
                "name": "general_elon"
            }
        ]
    }

    ## user1 is in chan1 and chan2
    ## user2 is in chan3
    ## Let user2 join chan2 by assuming channel_join() works
    channel_join(user2_token, ch2) ## chan2 is a PUBLIC channel

    ## Test that user1 is a part of chan1 and chan2
    assert channels_list(user1_token) == {
        "channels": [
            {
                "channel_id": ch1,
                "name": "general_bob"
            },
            {
                "channel_id": ch2,
                "name": "random_bob"
            }
        ]
    }
    ## Test that user2 is a part of chan3 and also chan2 AFTER joining
    assert channels_list(user2_token) == {
        "channels": [
            {
                "channel_id": ch2,
                "name": "random_bob"
            },
            {
                "channel_id": ch3,
                "name": "general_elon"
            }
        ]
    }

def test_channels_list_leave():
    """
    A test for the channels_list() function for ONE user who has joined two
    channels and leaves one of them.
    """
    workspace_reset()
    _, user1_token = user1()
    ch1, ch2 = chan1(user1_token), chan2(user1_token)
    ## Test that user1 is a part of chan1 and chan2 BEFORE leaving chan2
    assert channels_list(user1_token) == {
        "channels": [
            {
                "channel_id": ch1,
                "name": "general_bob"
            },
            {
                "channel_id": ch2,
                "name": "random_bob"
            }
        ]
    }

    ## user1 is in chan1 and chan2
    ## Let user2 leave chan2 by assuming channel_leave() works
    channel_leave(user1_token, ch2)

    ## Test that user1 is now only a part of chan1
    assert channels_list(user1_token) == {
        "channels": [
            {
                "channel_id": ch1,
                "name": "general_bob"
            }
        ]
    }

def test_channels_list_empty():
    """
    A test for the channels_list() function for no channels.
    """
    workspace_reset()
    _, user1_token = user1()
    assert channels_list(user1_token) == {"channels": []}


####################################################################
##                   Testing channels_listall                     ##
####################################################################

def test_channels_listall_all_joined():
    """
    A test for the channels_listall() function for ONE user who has joined
    all existing channels.
    """
    workspace_reset()
    _, user1_token = user1()
    ch1, ch2 = chan1(user1_token), chan2(user1_token)
    ## Only chan1 and chan2 have been created and user1 is in both of these
    assert channels_listall(user1_token) == {
        "channels": [
            {
                "channel_id": ch1,
                "name": "general_bob"
            },
            {
                "channel_id": ch2,
                "name": "random_bob"
            }
        ]
    }

def test_channels_listall_not_joined():
    """
    A test for the channels_listall() function for TWO users who have not joined
    all existing channels.
    """
    workspace_reset()
    _, user1_token = user1()
    _, user2_token = user2()
    ch1, ch2 = chan1(user1_token), chan2(user1_token)
    ch3, ch4 = chan3(user2_token), chan4(user2_token)
    ## Test that the correct list of channels is returned when user1 requests
    ## Even though user1 is not in chan3 and chan4 they should still be
    ## in the returned list of dictionaries
    assert channels_listall(user1_token) == {
        "channels": [
            {
                "channel_id": ch1,
                "name": "general_bob"
            },
            {
                "channel_id": ch2,
                "name": "random_bob"
            },
            {
                "channel_id": ch3,
                "name": "general_elon"
            },
            {
                "channel_id": ch4,
                "name": "random_elon"
            }
        ]
    }
    ## This list of channels should be the same as when user2 makes the request
    assert channels_listall(user1_token) == channels_listall(user2_token)

def test_channels_listall_empty():
    """
    A test for the channels_listall() function for no channels.
    """
    workspace_reset()
    _, user1_token = user1()
    assert channels_listall(user1_token) == {"channels": []}


####################################################################
##                    Testing channels_create                     ##
####################################################################

def test_channels_create():
    """
    A test for the channels_create() function.
    """
    workspace_reset()
    _, user1_token = user1()
    channel_public = channels_create(user1_token, "Kevin_pub", True)
    ## Check that this channel creation succeeded
    assert channels_list(user1_token) == {
        "channels": [
            {
                "channel_id": channel_public["channel_id"],
                "name": "Kevin_pub"
            }
        ]
    }

    channel_private = channels_create(user1_token, "Kevin_priv", False)
    ## Check that this channel creation succeeded
    assert channels_list(user1_token) == {
        "channels": [
            {
                "channel_id": channel_public["channel_id"],
                "name": "Kevin_pub"
            },
            {
                "channel_id": channel_private["channel_id"],
                "name": "Kevin_priv"
            }
        ]
    }

def test_channels_create_long_name_public():
    """
    A test for the channels_create() function for invalid public channel names.
    """
    workspace_reset()
    _, user1_token = user1()
    ## Channel name must be less than or equal to 20 characters
    with pytest.raises(InputError):
        channels_create(user1_token, "thisisareallylongname", True)
    with pytest.raises(InputError):
        channels_create(user1_token, "abcdefghijklmnopqrstuvwyxz", True)
    with pytest.raises(InputError):
        channels_create(user1_token, "generalchannelbutonlysendmemes", True)

def test_channels_create_long_name_private():
    """
    A test for the channels_create() function for invalid private channel names.
    """
    workspace_reset()
    _, user1_token = user1()
    ## Channel name must be less than or equal to 20 characters
    with pytest.raises(InputError):
        channels_create(user1_token, "thisisareallylongname", False)
    with pytest.raises(InputError):
        channels_create(user1_token, "mytopsecretchannelkeephidden", False)
    with pytest.raises(InputError):
        channels_create(user1_token, "allgovernmentdocumentshere", False)


####################################################################
##                       Other AccessErrors                       ##
####################################################################

def test_channels_access_error():
    """
    A test for all channels.py functions that check that an AccessError is
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
        channels_list(invalid_token)
    with pytest.raises(AccessError):
        channels_listall(invalid_token)
    with pytest.raises(AccessError):
        channels_create(invalid_token, "lol", True)
