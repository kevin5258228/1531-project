"""
Integration tests for the functions implemented in auth.py.
H11A-quadruples, April 2020.
"""

import pytest
from error import InputError, AccessError
from funcs.auth import auth_login, auth_logout, auth_register
from funcs.user import user_profile
from funcs.other import workspace_reset
from helpers.registers import user1, user2

####################################################################
##                       Testing auth_login                       ##
####################################################################

def test_auth_login_invalid_emails():
    """
    A test for the auth_login() function when passed in wrongly formatted emails.
    """
    workspace_reset()
    with pytest.raises(InputError):
        auth_login("abcdef.com", "password123")
    with pytest.raises(InputError):
        auth_login("abcdef@com", "password123")
    with pytest.raises(InputError):
        auth_login("abcdef@unsw-com", "password123")
    with pytest.raises(InputError):
        auth_login("abcdef#usyd.com", "password123")
    with pytest.raises(InputError):
        auth_login("abcdef@usyd@gitgud.com", "password123")

def test_auth_login_unregistered_emails():
    """
    A test for the auth_login() function when passed in unregistered emails
    with valid formatting.
    """
    workspace_reset()
    with pytest.raises(InputError):
        auth_login("dunkirk@gmail.com", "VeryStrongPassword!@#")
    with pytest.raises(InputError):
        auth_login("zunregistered_email5@unsw.edu.au", "VeryStrongPassword!@#")

def test_auth_login_wrong_password():
    """
    A test for the auth_login() function for registered users who enter an
    incorrect password.
    """
    workspace_reset()
    user1() ## correct password pword123
    user2() ## correct password pword456
    with pytest.raises(InputError):
        auth_login("bob.ross@unsw.edu.au", "pword!@#")
    with pytest.raises(InputError):
        auth_login("bob.ross@unsw.edu.au", "gOODpASSwORD$$$")
    with pytest.raises(InputError):
        auth_login("elon.musk@unsw.edu.au", "Password1")
    with pytest.raises(InputError):
        auth_login("elon.musk@unsw.edu.au", "195810581")
    ## Assume password are case sensitive (a reasonable assumption)
    with pytest.raises(InputError):
        auth_login("bob.ross@unsw.edu.au", "PWORD123")
    with pytest.raises(InputError):
        auth_login("elon.musk@unsw.edu.au", "PWORD456")

def test_auth_login_valid():
    """
    A test for the auth_login() function to check that it returns the
    same u_id as auth_register().
    """
    workspace_reset()
    user1_id, _ = user1()
    user2_id, _ = user2()
    assert auth_login("bob.ross@unsw.edu.au", "pword123")["u_id"] == user1_id
    assert auth_login("elon.musk@unsw.edu.au", "pword456")["u_id"] == user2_id


####################################################################
##                      Testing auth_logout                       ##
####################################################################

def test_auth_logout():
    """
    A test for the auth_logout() function.
    """
    workspace_reset()
    ## Registering a user generates a valid token for authentication
    _, user1_token = user1()
    _, user2_token = user2()
    assert auth_logout(user1_token)["is_success"]
    assert auth_logout(user2_token)["is_success"]


####################################################################
##                     Testing auth_register                      ##
####################################################################

def test_auth_register_invalid_email():
    """
    A test for the auth_register() function for wrongly formatted emails.
    """
    workspace_reset()
    with pytest.raises(InputError):
        auth_register("abcdef.com", "password123", "Richard", "Smith")
    with pytest.raises(InputError):
        auth_register("abcdef@com", "password123", "Richard", "Smith")
    with pytest.raises(InputError):
        auth_register("abcdef@unsw-com", "password123", "Richard", "Smith")
    with pytest.raises(InputError):
        auth_register("abcdef#usyd.com", "password123", "Richard", "Smith")
    with pytest.raises(InputError):
        auth_register("abcdef@usyd@gitgud.com", "password123", "Tom", "Hanks")

def test_auth_register_double():
    """
    A test for the auth_register() function for emails already in use.
    """
    workspace_reset()
    user1() ## registers email bob.ross@unsw.edu.au
    user2() ## registers email elon.musk@unsw.edu.au
    with pytest.raises(InputError):
        auth_register("bob.ross@unsw.edu.au", "password123", "Tom", "Hanks")
    with pytest.raises(InputError):
        auth_register("elon.musk@unsw.edu.au", "password123", "Richard", "Smith")

def test_auth_register_weak_password():
    """
    A test for the auth_register() function for passwords less than 6 characters long.
    """
    workspace_reset()
    with pytest.raises(InputError):
        auth_register("z5555555@unsw.edu.au", "f", "Frank", "Underwood")
    with pytest.raises(InputError):
        auth_register("z5555555@unsw.edu.au", "qwert", "Frank", "Underwood")
    with pytest.raises(InputError):
        auth_register("z5555555@unsw.edu.au", "hello", "Frank", "Underwood")
    with pytest.raises(InputError):
        auth_register("z5555555@unsw.edu.au", "@", "Frank", "Underwood")
    with pytest.raises(InputError):
        auth_register("z5555555@unsw.edu.au", "!@#$%", "Frank", "Underwood")
    with pytest.raises(InputError):
        auth_register("z5555555@unsw.edu.au", "     ", "Frank", "Underwood")
    with pytest.raises(InputError):
        auth_register("z5555555@unsw.edu.au", "", "Frank", "Underwood")

def test_auth_register_first_name():
    """
    A test for the auth_register() function for invalid name_first's.
    """
    workspace_reset()
    long_str = "a" * 52
    with pytest.raises(InputError):
        auth_register("t2@unsw.edu.au", "password123", "", "He")
    with pytest.raises(InputError):
        auth_register("t2@unsw.edu.au", "password123", long_str, "He")

def test_auth_register_last_name():
    """
    A test for the auth_register() function for invalid name_last's.
    """
    workspace_reset()
    long_str = "a" * 52
    with pytest.raises(InputError):
        auth_register("t2@unsw.edu.au", "password123", "Kevin", "")
    with pytest.raises(InputError):
        auth_register("t2@unsw.edu.au", "password123", "Kevin", long_str)

def test_auth_register_handle_creation():
    """
    A test for the auth_register() function that checks if handle creation
    is correct for people with the same name_first and name_last.
    """
    workspace_reset()
    user_1 = auth_register("tnguyen@unsw.edu.au", "password1", "Tam", "Nguyen")
    user_2 = auth_register("tnguyen1@unsw.edu.au", "password2", "Tam", "Nguyen")
    ## Since user1 and user2 have the same name_first and name_last then their
    ## handles should be modified so that they are unique
    ##
    ## Since user2 registers after user1, then user2"s handle should be modified
    ## Assume this is done by suffixing numbers on a user"s handle
    ##
    ## eg.
    ## tamnguyen  taken --> tamnguyen1
    ## tamnguyen1 taken --> tamnguyen2
    ## tamnguyen2 taken --> tamnguyen3
    ## etc...
    ##
    ## Assume user_profile works and check that the handles have been modified
    user1_h = user_profile(user_1["token"], user_1["u_id"])["user"]["handle_str"]
    user2_h = user_profile(user_2["token"], user_2["u_id"])["user"]["handle_str"]
    assert user1_h == "tamnguyen"
    assert user2_h == "tamnguyen1"

def test_auth_register_long_handle():
    """
    A test for the auth_register() function that checks if handle creation
    is correct for people with handles that would be over 20 characters long.
    """
    workspace_reset()
    name_first = "a" * 11
    name_last = "b" * 11
    user = auth_register("tn@unsw.edu.au", "password1", name_first, name_last)
    ## If the concatenation of name_first and name_last is longer than 20
    ## characters, it is cutoff at 20 characters
    ##
    ## Assume user_profile works and check that this is true
    user_h = user_profile(user["token"], user["u_id"])["user"]["handle_str"]
    assert user_h == "a" * 11 + "b" * 9   # 2 b"s are cut off


####################################################################
##                       Other AccessErrors                       ##
####################################################################

def test_auth_access_error():
    """
    A test for all auth.py functions except auth_login() and auth_register()
    that check that an AccessError is thrown when passed in an invalid token.
    """
    workspace_reset()
    ## Assume these are invalid tokens (a fair assumption since there
    ## are no registered users)
    with pytest.raises(AccessError):
        auth_logout("111111")
    with pytest.raises(AccessError):
        auth_logout(" ")
