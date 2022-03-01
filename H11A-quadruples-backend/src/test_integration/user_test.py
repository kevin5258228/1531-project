"""
Integration tests for the functions implemented in user.py.
H11A-quadruples, April 2020.
"""

import pytest
from error import InputError, AccessError
from funcs.channel import channel_details
from funcs.user import (
    user_profile,
    user_profile_setname,
    user_profile_setemail,
    user_profile_sethandle
)
from funcs.other import workspace_reset
from helpers.registers import user1, user2, chan1
from port_settings import BASE_URL

####################################################################
##                      Testing user_profile                      ##
####################################################################

def test_user_profile_valid():
    """
    A test for the user_profile() function under VALID inputs.
    """
    workspace_reset()
    user1_id, user1_token = user1()
    user2_id, user2_token = user2()
    ## Test if user_profile() returns the correct dictionary for user1
    assert user_profile(user1_token, user1_id) == {
        "user": {
            "u_id": user1_id,
            "email": "bob.ross@unsw.edu.au",
            "name_first": "Bob",
            "name_last": "Ross",
            "handle_str": "bobross", ## lowercase concatenation of full name
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        }
    }
    ## Test if user_profile() returns the correct dictionary for user2
    assert user_profile(user2_token, user2_id) == {
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
    A test for the user_profile() function under INVALID inputs.
    """
    workspace_reset()
    user1_id, user1_token = user1()
    with pytest.raises(InputError):
        ## Errors are raised when a user with u_id is not a valid user
        ## Here we assume (user1_id + 99) is unregistered and invalid
        user_profile(user1_token, user1_id + 99)


####################################################################
##                  Testing user_profile_setname                  ##
####################################################################

def test_user_profile_setname_valid():
    """
    A test for the user_profile_setname() function under VALID inputs.
    """
    workspace_reset()
    user1_id, user1_token = user1()
    ch1 = chan1(user1_token)
    user_profile_setname(user1_token, "Ross", "Bob")
    ## The following assertion assumes user_profile() works
    assert user_profile(user1_token, user1_id) == {
        "user": {
            "u_id": user1_id,
            "email": "bob.ross@unsw.edu.au",
            "name_first": "Ross",
            "name_last": "Bob",
            "handle_str": "bobross", ## assumes handle remains unchanged
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        }
    }
    ## Assert channel details have been updated
    assert channel_details(user1_token, ch1)["owner_members"] == [
        {
            "u_id": user1_id,
            "name_first": "Ross",
            "name_last": "Bob",
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        }
    ]
    assert channel_details(user1_token, ch1)["all_members"] == [
        {
            "u_id": user1_id,
            "name_first": "Ross",
            "name_last": "Bob",
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        }
    ]

def test_user_profile_setname_same_names():
    """
    A test for the user_profile_setname() function when a user changes their
    name to another user's name (which is allowed).
    """
    workspace_reset()
    user1_id, user1_token = user1()
    user2_id, user2_token = user2()
    user_profile_setname(user1_token, "John", "Smith")
    user_profile_setname(user2_token, "John", "Smith")
    ## The following assertions assume user_profile() works
    ## Test that user1"s name change succeeded by calling user_profile()
    assert user_profile(user1_token, user1_id) == {
        "user": {
            "u_id": user1_id,
            "email": "bob.ross@unsw.edu.au",
            "name_first": "John",
            "name_last": "Smith",
            "handle_str": "bobross",
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        }
    }
    ## Test that user2"s name change succeeded by calling user_profile()
    assert user_profile(user2_token, user2_id) == {
        "user": {
            "u_id": user2_id,
            "email": "elon.musk@unsw.edu.au",
            "name_first": "John",
            "name_last": "Smith",
            "handle_str": "elonmusk",
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        }
    }

def test_user_profile_setname_invalid():
    """
    A test for the user_profile_setname() function under INVALID inputs.
    """
    workspace_reset()
    _, user1_token = user1()
    ## Create a 51 character string (>50) to be used for testing
    long_str = "a" * 51
    ## name_first must be between 1 and 50 characters
    ## Assume this is INCLUSIVE (ie. 1 character name_first is allowed)
    with pytest.raises(InputError):
        user_profile_setname(user1_token, "", "Kroeger")
    with pytest.raises(InputError):
        user_profile_setname(user1_token, long_str, "Kroeger")

    ## name_last must be between 1 and 50 characters
    with pytest.raises(InputError):
        user_profile_setname(user1_token, "James", "")
    with pytest.raises(InputError):
        user_profile_setname(user1_token, "James", long_str)

    ## Both name_first and name_last must be 1-50 characters
    with pytest.raises(InputError):
        user_profile_setname(user1_token, "", "")
    with pytest.raises(InputError):
        user_profile_setname(user1_token, long_str, long_str)


####################################################################
##                 Testing user_profile_setemail                  ##
####################################################################

def test_user_profile_setemail_valid():
    """
    A test for the user_profile_setemail() function under VALID inputs.
    """
    workspace_reset()
    user1_id, user1_token = user1()
    user2_id, user2_token = user2()
    user_profile_setemail(user1_token, "bob.ross@gmail.com") ## @gmail.com now
    user_profile_setemail(user2_token, "elon.musk@gmail.com")
    ## The following assertions assume user_profile() works
    ## Test that user1"s email change succeeded by calling user_profile()
    assert user_profile(user1_token, user1_id) == {
        "user": {
            "u_id": user1_id,
            "email": "bob.ross@gmail.com",
            "name_first": "Bob",
            "name_last": "Ross",
            "handle_str": "bobross",
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        }
    }
    ## Test that user2"s email change succeeded by calling user_profile()
    assert user_profile(user2_token, user2_id) == {
        "user": {
            "u_id": user2_id,
            "email": "elon.musk@gmail.com",
            "name_first": "Elon",
            "name_last": "Musk",
            "handle_str": "elonmusk",
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        }
    }

def test_user_profile_setemail_invalid():
    """
    A test for the user_profile_setemail() function under INVALID inputs.
    """
    workspace_reset()
    _, user1_token = user1()
    ## If a user changes their email to an invalid email address
    ## then an InputError is thrown
    ##
    ## Invalid emails were checked to be truly invalid using email_checker.py
    with pytest.raises(InputError):
        user_profile_setemail(user1_token, "")
    with pytest.raises(InputError):
        user_profile_setemail(user1_token, "abc")
    with pytest.raises(InputError):
        user_profile_setemail(user1_token, "@gmail.com")
    with pytest.raises(InputError):
        user_profile_setemail(user1_token, "abc.com")
    with pytest.raises(InputError):
        user_profile_setemail(user1_token, "bobross@")
    with pytest.raises(InputError):
        user_profile_setemail(user1_token, ".bobross")

def test_user_profile_setemail_in_use():
    """
    A test for the user_profile_setemail() function when a user changes their
    email to an email already in use (which throws an InputError).
    """
    workspace_reset()
    _, user1_token = user1()
    _, user2_token = user2()
    ## If Bob Ross changes his email to Elon Musk"s email, or
    ## if Elon Musk changes his email to Bob Ross" email, then
    ## an InputError is thrown
    with pytest.raises(InputError):
        user_profile_setemail(user1_token, "elon.musk@unsw.edu.au")
    with pytest.raises(InputError):
        user_profile_setemail(user2_token, "bob.ross@unsw.edu.au")


####################################################################
##                Testing user_profile_sethandle                  ##
####################################################################

def test_user_profile_sethandle_valid():
    """
    A test for the user_profile_sethandle() function under VALID inputs.
    """
    workspace_reset()
    user1_id, user1_token = user1()
    user2_id, user2_token = user2()
    user_profile_sethandle(user1_token, "bobrossisalive")
    user_profile_sethandle(user2_token, "elonmuskishigh")
    ## The following assertions assume user_profile() works
    ## Test that user1"s handle change succeeded by calling user_profile()
    assert user_profile(user1_token, user1_id) == {
        "user": {
            "u_id": user1_id,
            "email": "bob.ross@unsw.edu.au",
            "name_first": "Bob",
            "name_last": "Ross",
            "handle_str": "bobrossisalive",
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        }
    }
    ## Test that user2"s handle change succeeded by calling user_profile()
    assert user_profile(user2_token, user2_id) == {
        "user": {
            "u_id": user2_id,
            "email": "elon.musk@unsw.edu.au",
            "name_first": "Elon",
            "name_last": "Musk",
            "handle_str": "elonmuskishigh",
            "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
        }
    }

def test_user_profile_sethandle_invalid():
    """
    A test for the user_profile_sethandle() function under INVALID inputs.
    """
    workspace_reset()
    _, user1_token = user1()
    ## handle_str must be between 2 and 20 characters
    ## Assume this is INCLUSIVE (ie. 2 character handle_str is allowed)
    with pytest.raises(InputError):
        user_profile_sethandle(user1_token, "")
    with pytest.raises(InputError):
        user_profile_sethandle(user1_token, "a")
    with pytest.raises(InputError):
        user_profile_sethandle(user1_token, "abcdefghijklmnopqrstu") ## 21 char
    with pytest.raises(InputError):
        user_profile_sethandle(user1_token, "abcdefghijklmnopqrstuvwxyz")

def test_user_profile_sethandle_in_use():
    """
    A test for the user_profile_sethandle() function when a user changes their
    handle to an handle already in use (which throws an InputError).
    """
    workspace_reset()
    _, user1_token = user1()
    _, user2_token = user2()
    ## Here, Bob Ross attempts to change his handle to Elon Musk"s handle
    ## and Elon Musk attempts to change his handle to Bob Ross" handle,
    ## which should throw an InputError
    with pytest.raises(InputError):
        user_profile_sethandle(user1_token, "elonmusk")
    with pytest.raises(InputError):
        user_profile_sethandle(user2_token, "bobross")


####################################################################
##                       Other AccessErrors                       ##
####################################################################

def test_user_access_error():
    """
    A test for all user.py functions that check that an AccessError is
    thrown when passed in an invalid token.
    """
    workspace_reset()
    user1_id, user1_token = user1()
    ## Add 50 "a"s onto the end of user1_token to produce an invalid token
    ##
    ## This token is assumed to be invalid since there are no other registered
    ## users for this token to belong to
    invalid_token = user1_token + ("a" * 50)
    with pytest.raises(AccessError):
        user_profile(invalid_token, user1_id)
    with pytest.raises(AccessError):
        user_profile_setname(invalid_token, "James", "Kroeger")
    with pytest.raises(AccessError):
        user_profile_setemail(invalid_token, "jameskroeger123@gmail.com")
    with pytest.raises(AccessError):
        user_profile_sethandle(invalid_token, "jameskroeger")
