"""
Integration tests for the functions implemented in channel.py.
H11A-quadruples, April 2020.
"""

import pytest
from error import InputError, AccessError
from funcs.channels import channels_create, channels_list, channels_listall
from funcs.channel import (
    channel_invite,
    channel_details,
    channel_leave,
    channel_join,
    channel_addowner,
    channel_removeowner,
    channel_messages
)
from funcs.message import message_send
from funcs.other import users_all, workspace_reset
from helpers.registers import user1, user2, user3
from port_settings import BASE_URL

########################################################################
##                      Testing channel_invite                        ##
########################################################################

## ASSUMPTIONS: auth_register, channels_create,channels_list, users_all,
## channel_join, channel_details are functional
def test_channel_invite():
    """
    A test for the channel_invite() function under valid input.
    """
    workspace_reset()
    ## Register users A and B
    _, token_a = user1()
    u_id_b, token_b = user2()

    ## Person A creates a new private channel
    new_channel_result = channels_create(token_a, "channelname", False)
    channel_id = new_channel_result["channel_id"]

    ## Invite person B to the channel
    channel_invite(token_a, channel_id, u_id_b)

    ## List the channels that person B is a part of
    channels_person_b = channels_list(token_b)
    channels = channels_person_b["channels"]
    assert any(ch["channel_id"] == channel_id for ch in channels)

def test_channel_invite_invalid_channel():
    """
    A test for the channel_invite() function under invalid channel_id input.
    """
    workspace_reset()
    ## Register users A, B and C
    _, token_a = user1()
    _, token_b = user2()
    u_id_c, _ = user3()

    ## Users A and B create a new private channel
    channels_create(token_a, "channelname", False)
    new_channel_result_b = channels_create(token_b, "channelname_b", False)

    ## Get user B channel ID
    channel_id_b = new_channel_result_b["channel_id"]

    ## Dictionary conaining a list of dictionaries
    channels_result = channels_list(token_a)
    ## Get the details for all channels (list of dictionaries)
    list_channels = channels_result["channels"]

    ## Channel_id does not refer to a valid channel that the authorised user is part of
    ## Using channel_id for user B instead of user A"s own channel_id
    assert not any(channel["channel_id"] == channel_id_b for channel in list_channels)
    with pytest.raises(AccessError):
        channel_invite(token_a, channel_id_b, u_id_c)

def test_channel_invite_invalid_user():
    """
    A test for the channel_invite() function under invalid user input.
    """
    workspace_reset()
    ## Register user
    _, token = user1()

    ## Create a new private channel
    new_channel_result = channels_create(token, "channelname", False)
    channel_id = new_channel_result["channel_id"]

    users_result = users_all(token)
    list_users = users_result["users"]
    assert not any(user["u_id"] == 999 for user in list_users)
    with pytest.raises(InputError):
        channel_invite(token, channel_id, 999)

def test_channel_invite_already_member():
    """
    A test for the channel_invite() function under other invalid input.
    """
    workspace_reset()
    ## Register user A and B
    _, token_a = user1()
    u_id_b, token_b = user2()

    ## User A creates a new public channel
    new_channel_result = channels_create(token_a, "channelname", True)
    channel_id = new_channel_result["channel_id"]
    ## Invite User B to the channel
    channel_invite(token_a, channel_id, u_id_b)
    channel_details_result = channel_details(token_b, channel_id)
    list_all_members = channel_details_result["all_members"]
    assert any(member["u_id"] == u_id_b for member in list_all_members)
    ## Authorised user is already a member of the channel
    with pytest.raises(InputError):
        channel_invite(token_a, channel_id, u_id_b)


########################################################################
##                      Testing channel_details                       ##
########################################################################

## ASSUMPTIONS: auth_register, channels_create, channels_list are functional
def test_channel_details():
    """
    A test for the channel_details() function under valid input.
    """
    workspace_reset()
    ## Register user A
    u_id, token = user1()

    ## Create a new private channel and get the channel id from it
    new_channel_result = channels_create(token, "channelname", False)
    channel_id = new_channel_result["channel_id"]

    channel_details_result = channel_details(token, channel_id)
    channel_name = channel_details_result["name"]
    list_owner_members = channel_details_result["owner_members"]
    list_all_members = channel_details_result["all_members"]

    assert channel_name == "channelname"
    assert list_owner_members == [
        {
            "u_id": u_id,
            "name_first": "Bob",
            "name_last": "Ross",
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        }
    ]
    assert list_all_members == [
        {
            "u_id": u_id,
            "name_first": "Bob",
            "name_last": "Ross",
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        }
    ]

def test_channel_details_invalid_channel():
    """
    A test for the channel_details() function under invalid channel_id input.
    """
    workspace_reset()
    ## Register user A
    _, token = user1()

    ## Person A creates a new private channel
    channels_create(token, "channelname", False)

    ## Dictionary conaining a list of dictionaries
    channels_result = channels_list(token)
    ## Get the details for all channels (list of dictionaries)
    list_channels = channels_result["channels"]

    assert not any(channel["channel_id"] == 999 for channel in list_channels)
    ## Channel_id does not refer to a valid channel that the authorised user
    ## is part of
    with pytest.raises(InputError):
        channel_details(token, 999)

def test_channel_details_not_member():
    """
    A test for the channel_details() function under other invalid input.
    """
    workspace_reset()
    ## Registers user A and B
    _, token_a = user1()
    u_id_b, token_b = user2()

    ## User A creates a new private channel
    new_channel_result = channels_create(token_a, "channelname", False)
    channel_id = new_channel_result["channel_id"]

    channel_details_result = channel_details(token_a, channel_id)
    list_all_members = channel_details_result["all_members"]
    assert not any(member["u_id"] == u_id_b for member in list_all_members)

    ## Authorised user is not a member of channel with channel_id
    with pytest.raises(AccessError):
        channel_details(token_b, channel_id)


########################################################################
##                     Testing channel_messages                       ##
########################################################################

## ASSUMPTIONS: auth_register, channels_create, message_send,
## channels_list are functional
def test_channel_messages():
    """
    A test for the channel_messages() function under valid input.
    """
    workspace_reset()
    ## Register user
    _, token = user1()

    ## Create a new public channel
    new_channel_result = channels_create(token, "channelname", True)
    channel_id = new_channel_result["channel_id"]

    ## List of message ids, least recent to most recent from left to right of list
    list_m_id = []
    i = 0
    while i < 60:
        msg_send_result = message_send(token, channel_id, "hello")
        m_id = msg_send_result["message_id"]
        list_m_id.append(m_id)
        i += 1

    ## Reverse the list so its in order of most recent to least recent (left to right)
    list_m_id.reverse()
    ## Get the first fifty elements of the list
    list_first_fifty = list_m_id[0:50]
    ## Get the last ten elements of the list
    list_last_ten = list_m_id[-10:]

    messages_zero_to_fifty = channel_messages(token, channel_id, 0)
    assert messages_zero_to_fifty["start"] == 0
    assert messages_zero_to_fifty["end"] == 50
    list_messages_a = messages_zero_to_fifty["messages"]
    list_m_id_a = []
    for message in list_messages_a:
        list_m_id_a.append(message["message_id"])

    assert list_first_fifty == list_m_id_a

    messages_fifty_to_sixty = channel_messages(token, channel_id, 50)
    assert messages_fifty_to_sixty["start"] == 50
    assert messages_fifty_to_sixty["end"] == -1

    list_messages_b = messages_fifty_to_sixty["messages"]
    list_m_id_b = []
    for message in list_messages_b:
        list_m_id_b.append(message["message_id"])

    assert list_last_ten == list_m_id_b

def test_channel_messages_invalid_channel_id():
    """
    A test for the channel_messages() function under invalid channel_id input.
    """
    workspace_reset()
    ## Register user A
    _, token = user1()

    channels_list_result = channels_list(token)
    channels_details = channels_list_result["channels"]
    if not any(channel["channel_id"] == 999 for channel in channels_details):
        with pytest.raises(InputError):
            channel_messages(token, 999, 0)

def test_channel_messages_start_greater_than_messages():
    """
    A test for the channel_messages() function under invalid input where start
    is greater than the number of channel messages.
    """
    workspace_reset()
    _, token = user1()
    start = 10

    ## Create a new private channel
    new_channel_result = channels_create(token, "channelname", False)
    channel_id = new_channel_result["channel_id"]
    message_send(token, channel_id, "hello world")

    with pytest.raises(InputError):
        channel_messages(token, channel_id, start)

def test_channel_messages_not_member():
    """
    A test for the channel_messages() function under invalid input where a
    non-member requests a channel's messages.
    """
    workspace_reset()

    ## Register users A and B
    _, token_a = user1()
    _, token_b = user2()

    ## User A creates a private channel
    new_channel_result = channels_create(token_a, "channelname", False)
    channel_id = new_channel_result["channel_id"]
    with pytest.raises(AccessError):
        channel_messages(token_b, channel_id, 0)


########################################################################
##                       Testing channel_leave                        ##
########################################################################

## ASSUMPTIONS: auth_register, channels_create, channels_list, channel_details
## are functional.
## Empty channel can exist
def test_channel_leave():
    """
    A test for the channel_leave() function under valid input.
    """
    workspace_reset()

    ## Register user
    _, token = user1()

    ## Create a new public channel and get the channel id from it
    new_channel_result = channels_create(token, "channelname", True)
    channel_id = new_channel_result["channel_id"]

    channel_leave(token, channel_id)
    channels_result = channels_list(token)
    chan_details = channels_result["channels"]

    assert not any(ch["channel_id"] == channel_id for ch in chan_details)

def test_channel_leave_invalid_channel():
    """
    A test for the channel_leave() function under invalid channel_id input.
    """
    workspace_reset()

    _, token = user1()

    channels_result = channels_list(token)
    list_channels = channels_result["channels"]

    assert not any(channel["channel_id"] == 999 for channel in list_channels)
    ## Channel id is not a valid channel
    with pytest.raises(InputError):
        channel_leave(token, 999)

def test_channel_leave_not_member():
    """
    A test for the channel_leave() function under invalid input where a non-member
    tries to leave a channel.
    """
    workspace_reset()

    u_id_a, token_a = user1()
    _, token_b = user2()

    new_channel_result = channels_create(token_b, "channelname", False)
    channel_id = new_channel_result["channel_id"]

    channel_details_result = channel_details(token_b, channel_id)
    list_all_members = channel_details_result["all_members"]

    assert not any(member["u_id"] == u_id_a for member in list_all_members)
    ## Authorised user is not a member of channel with channel_id
    with pytest.raises(AccessError):
        channel_leave(token_a, channel_id)


########################################################################
##                       Testing channel_join                         ##
########################################################################

## ASSUMPTIONS: auth_register, channels_create, channels_list, channels_listall
## are functional.
def test_channel_join():
    """
    A test for the channel_join() function under valid input.
    """
    workspace_reset()

    _, token_a = user1()
    _, token_b = user2()

    ## User A creates a public channel
    channels_result = channels_create(token_a, "channelname", True)
    channel_id = channels_result["channel_id"]

    ## Join the channel with channel_id
    channel_join(token_b, channel_id)
    channels_result = channels_list(token_b)
    chan_details = channels_result["channels"]

    ## Users lists of channels should now contain the new channel_id
    assert any(channel["channel_id"] == channel_id for channel in chan_details)

def test_channel_join_invalid_channel():
    """
    A test for the channel_join() function under invalid channel_id input.
    """
    workspace_reset()

    ## Register user A
    _, token = user1()

    channels_result = channels_listall(token)
    list_channels = channels_result["channels"]

    assert not any(channel["channel_id"] == 999 for channel in list_channels)
    ## Channel ID is not a valid channel
    with pytest.raises(InputError):
        channel_join(token, 999)

def test_channel_join_private_channel():
    """
    A test for the channel_join() function for a private channel.
    """
    workspace_reset()

    ## Registers users A and B
    _, token_a = user1()
    _, token_b = user2()

    ## User A creates a new private channel
    new_channel_result = channels_create(token_a, "channelname", False)
    channel_id = new_channel_result["channel_id"]
    ## User B tries to join a private channel
    with pytest.raises(AccessError):
        channel_join(token_b, channel_id)


########################################################################
##                     Testing channel_addowner                       ##
########################################################################

## ASSUMPTION: auth_register, channels_create, channel_join,
## channel_details, channels_list are functional
def test_channel_addowner():
    """
    A test for the channel_addowner() function under valid input.
    """
    workspace_reset()

    ## Register users A and B
    _, token_a = user1()
    u_id_b, token_b = user2()

    ## User A creates a public channel
    new_channel_result = channels_create(token_a, "channelname", True)
    channel_id = new_channel_result["channel_id"]

    ## User B joins the channel
    channel_join(token_b, channel_id)
    ## Make user B an owner of this channel
    channel_addowner(token_a, channel_id, u_id_b)

    channel_details_result = channel_details(token_b, channel_id)
    ## List of dictionaries
    list_owners = channel_details_result["owner_members"]
    assert any(owner["u_id"] == u_id_b for owner in list_owners)

def test_channel_addowner_invalid_channel():
    """
    A test for the channel_addowner() function under invalid channel_id input.
    """
    workspace_reset()

    ## Register user A and B
    _, token_a = user1()
    u_id_b, _ = user2()

    ## User A creates a public channel
    channels_create(token_a, "channelname", True)

    channels_list_result = channels_list(token_a)
    list_channels = channels_list_result["channels"]
    assert not any(channel["channel_id"] == 999 for channel in list_channels)
    ## Channel ID is not a valid channel
    with pytest.raises(InputError):
        channel_addowner(token_a, 999, u_id_b)

def test_channel_addowner_existing_owner():
    """
    A test for the channel_addowner() function under invalid input where a user
    is already an owner.
    """
    workspace_reset()

    ## Register user A and B
    _, token_a = user1()
    u_id_b, _ = user2()

    ## User A creates a public channel
    new_channel_result = channels_create(token_a, "channelname", True)
    channel_id = new_channel_result["channel_id"]
    ## Makes user B an owner of this channel
    channel_addowner(token_a, channel_id, u_id_b)

    channel_details_result = channel_details(token_a, channel_id)
    list_owners = channel_details_result["owner_members"]
    ## Trying to make user B an owner when they are already one
    assert any(owner["u_id"] == u_id_b for owner in list_owners)
    with pytest.raises(InputError):
        channel_addowner(token_a, channel_id, u_id_b)

def test_channel_addowner_not_owner():
    """
    A test for the channel_addowner() function under invalid input where a
    non-channel-owner attempts to add an owner.
    """
    workspace_reset()

    ## Register users A, B and C
    _, token_a = user1()
    _, token_b = user2()
    u_id_c, _ = user3()

    ## User A creates a public channel
    new_channel_result = channels_create(token_a, "channelname", True)
    channel_id = new_channel_result["channel_id"]
    ## User B joins the channel
    channel_join(token_b, channel_id)
    ## User B makes user C an owner of the channel but is not an owner themselves
    with pytest.raises(AccessError):
        channel_addowner(token_b, channel_id, u_id_c)

def test_channel_addowner_not_slackr_owner():
    """
    A test for the channel_addowner() function under invalid input where a
    non-Slackr-owner attempts to add an owner.
    """
    workspace_reset()

    ## Register users A, B and C
    _, token_a = user1()
    _, token_b = user2()
    u_id_c, _ = user3()

    ## User A creates a public channel
    new_channel_result = channels_create(token_a, "channelname", True)
    channel_id = new_channel_result["channel_id"]
    ## User B joins the channel
    channel_join(token_b, channel_id)

    ## User B tries to add user C as a channel owner, but they aren"t a slackr owner
    with pytest.raises(AccessError):
        channel_addowner(token_b, channel_id, u_id_c)


########################################################################
##                    Testing channel_removeowner                     ##
########################################################################

## ASSUMPTIONS: auth_register, channels_create, channel_addowner,
## channel_details, channel_invite, channels_list, channel_join are functional
def test_channel_removeowner():
    """
    A test for the channel_removeowner() function under valid input.
    """
    workspace_reset()

    ## Register user A and B
    u_id_a, token_a = user1()
    u_id_b, token_b = user2()

    ## User A creates a public channel
    new_channel_result = channels_create(token_a, "channelname", True)
    channel_id = new_channel_result["channel_id"]
    ## User B joins the channel
    channel_join(token_b, channel_id)
    ## Make user B an owner of the channel
    channel_addowner(token_a, channel_id, u_id_b)
    ## User B removes user A as an owner
    channel_removeowner(token_b, channel_id, u_id_a)

    channel_details_result = channel_details(token_b, channel_id)
    list_owners = channel_details_result["owner_members"]
    assert not any(owner["u_id"] == u_id_a for owner in list_owners)

def test_channel_removeowner_invalid_channel():
    """
    A test for the channel_removeowner() function under invalid channel_id input.
    """
    workspace_reset()

    ## Register user A and B
    _, token_a = user1()
    u_id_b, _ = user2()

    ## User A creates a private channel and invites user B to the channel
    new_channel_result = channels_create(token_a, "channelname", False)
    channel_id = new_channel_result["channel_id"]
    channel_invite(token_a, channel_id, u_id_b)
    channel_addowner(token_a, channel_id, u_id_b)

    channels_list_result = channels_list(token_a)
    list_channels = channels_list_result["channels"]
    assert not any(channel["channel_id"] == 999 for channel in list_channels)

    ## Channel ID is not a valid channel
    with pytest.raises(InputError):
        channel_removeowner(token_a, 999, u_id_b)

def test_channel_removeowner_not_owner():
    """
    A test for the channel_removeowner() function under invalid input where a user
    attempts to remove a non-owner's ownership.
    """
    workspace_reset()

    ## Register user A and B
    _, token_a = user1()
    u_id_b, token_b = user2()

    new_channel_result = channels_create(token_a, "channelname", True)
    channel_id = new_channel_result["channel_id"]
    channel_join(token_b, channel_id)
    with pytest.raises(InputError):
        channel_removeowner(token_a, channel_id, u_id_b)

def test_channel_removeowner_auth_not_owner():
    """
    A test for the channel_removeowner() function under invalid input where a
    non-channel-owner attempts to remove ownership.
    """
    workspace_reset()

    ## Register users A, B and C
    _, token_a = user1()
    u_id_b, token_b = user2()
    _, token_c = user3()

    ## User A creates a public channel
    new_channel_result = channels_create(token_a, "channelname", True)
    channel_id = new_channel_result["channel_id"]
    ## User B joins the channel and is added as an owner by user A
    channel_join(token_b, channel_id)
    channel_addowner(token_a, channel_id, u_id_b)
    ## User C joins the channel
    channel_join(token_c, channel_id)
    ## User C can"t remove user B as an owner of the channel- doesn"t have owner authority
    with pytest.raises(AccessError):
        channel_removeowner(token_c, channel_id, u_id_b)

def test_channel_removeowner_not_slackr_owner():
    """
    A test for the channel_removeowner() function under invalid input where a
    non-Slackr-owner attempts to remove ownership.
    """
    workspace_reset()

    ## Register users A and B
    u_id_a, token_a = user1()
    _, token_b = user2()

    ## User A creates a public channel
    new_channel_result = channels_create(token_a, "channelname", True)
    channel_id = new_channel_result["channel_id"]
    ## User B joins the channel
    channel_join(token_b, channel_id)

    ## User B tries to remove user A as an owner of this channel,
    ## but they aren"t an owner of the slackr
    with pytest.raises(AccessError):
        channel_removeowner(token_b, channel_id, u_id_a)


####################################################################
##                       Channel AccessErrors                     ##
####################################################################

def test_channel_access_error():
    """
    A test for all channel.py functions that check that an AccessError is
    thrown when passed in an invalid token.
    """
    workspace_reset()

    u_id_a, token_a = user1()
    ## Add 50 "a"s onto the end of user1_token to produce an invalid token
    ##
    ## This token is assumed to be invalid since there are no other registered
    ## users for this token to belong to
    invalid_token = token_a + ("a" * 50)
    with pytest.raises(AccessError):
        channel_invite(invalid_token, 10, u_id_a)
    with pytest.raises(AccessError):
        channel_details(invalid_token, 10)
    with pytest.raises(AccessError):
        channel_messages(invalid_token, 10, 0)
    with pytest.raises(AccessError):
        channel_leave(invalid_token, 10)
    with pytest.raises(AccessError):
        channel_join(invalid_token, 10)
    with pytest.raises(AccessError):
        channel_addowner(invalid_token, 10, u_id_a)
    with pytest.raises(AccessError):
        channel_removeowner(invalid_token, 10, u_id_a)
