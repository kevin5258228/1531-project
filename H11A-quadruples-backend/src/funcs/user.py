"""
Implementations of the user functions.
H11A-quadruples, April 2020.
"""

from error import AccessError, InputError
from database.database import AUTH_DATABASE, CHANNELS_DATABASE
from database.helpers_auth import (
    check_email,
    search_email,
    is_token_valid,
    is_handle_in_use,
    find_u_id
)
from constants import DELETED_USER_ID

def user_profile(token, u_id):
    """
    Returns information about a valid user.

    Args:
        token (str): Token of the user requesting another user's information.
        u_id (int): id of the user whose information is being requested.
    Raises:
        AccessError: if token is invalid.
        InputError: if u_id is not a valid user.
    Returns:
        A dictionary containing the requested user's information.
    """
    ## Check for AccessErrors
    if not is_token_valid(token):
        raise AccessError(description="Token is not a valid token")

    ## Check if user is deleted
    if u_id == DELETED_USER_ID:
        return {
            "user": {
                "u_id": DELETED_USER_ID,
                "email": None,
                "name_first": "[removed]",
                "name_last": "", ## cannot be replicated since name_last > 0 characters
                "handle_str": None,
                "profile_img_url": None
            }
        }

    ## Find the user in the database and return their profile
    auth_data = AUTH_DATABASE.get()
    for user in auth_data["registered_users"]:
        if user["u_id"] == u_id:
            return {
                "user": {
                    "u_id": u_id,
                    "email": user["email"],
                    "name_first": user["name_first"],
                    "name_last": user["name_last"],
                    "handle_str": user["handle_str"],
                    "profile_img_url": user["profile_img_url"]
                }
            }

    ## If the function has not returned, then u_id is not a valid user, so
    ## raise an InputError
    raise InputError(description="User with u_id is not a valid user")


def user_profile_setname(token, name_first, name_last):
    """
    Updates the user's first name and last name.

    Args:
        token (str): Token of the user who is changing their name.
        name_first (str): User's new first name.
        name_last (str): User's new last name.
    Raises:
        AccessError: if token is invalid.
        InputError: if name_first is not between 1 and 50 characters inclusive.
        InputError: if name_last is not between 1 and 50 characters inclusive.
    Returns:
        Empty dictionary.
    """
    ## Check for AccessErrors
    if not is_token_valid(token):
        raise AccessError(description="Token is not a valid token")

    ## Check for InputErrors
    if not 1 <= len(name_first) <= 50:
        raise InputError(description="name_first is not between 1 and 50 characters")
    if not 1 <= len(name_last) <= 50:
        raise InputError(description="name_last is not between 1 and 50 characters")

    ## Find the u_id corresponding to the given token
    user_id = find_u_id(token)

    ## Update the user's details in the auth database
    auth_data = AUTH_DATABASE.get()
    for user in auth_data["registered_users"]:
        if user["u_id"] == user_id:
            user["name_first"] = name_first
            user["name_last"] = name_last
            break
    AUTH_DATABASE.update(auth_data)

    ## Update the user's name in the channel details database if they
    ## are members/owners of any channel
    channel_data = CHANNELS_DATABASE.get()
    for channel in channel_data["channels"]:
        ## Update name if user is an owner
        for owner in channel["owner_members"]:
            if owner["u_id"] == user_id:
                owner["name_first"] = name_first
                owner["name_last"] = name_last
                break
        ## Update name if user is a member
        for member in channel["all_members"]:
            if member["u_id"] == user_id:
                member["name_first"] = name_first
                member["name_last"] = name_last
                break
    CHANNELS_DATABASE.update(channel_data)
    return {}


def user_profile_setemail(token, email):
    """
    Updates the user's email address.

    Args:
        token (str): Token of the user who is changing their email address.
        email (str): User's new email address.
    Raises:
        AccessError: if token is invalid.
        InputError: if email is incorrectly formatted.
        InputError: if email is already in use.
    Returns:
        Empty dictionary.
    """
    ## Check for AccessErrors
    if not is_token_valid(token):
        raise AccessError(description="Token is not a valid token")

    ## Check for InputErrors
    if not check_email(email):
        raise InputError(description="Email entered is not a valid email")
    if search_email(email):
        raise InputError(description="Email address is already in use")

    ## Find the u_id corresponding to the given token
    user_id = find_u_id(token)

    ## Update the user's details in the database
    auth_data = AUTH_DATABASE.get()
    for user in auth_data["registered_users"]:
        if user["u_id"] == user_id:
            user["email"] = email
            break
    AUTH_DATABASE.update(auth_data)
    return {}


def user_profile_sethandle(token, handle_str):
    """
    Updates the user's handle (display name).

    Args:
        token (str): Token of the user who is changing their handle.
        handle_str (str): User's new handle.
    Raises:
        AccessError: if token is invalid.
        InputError: if handle_str is not between 2 and 20 characters inclusive.
        InputError: if handle_str is already in use by another user.
    Returns:
        Empty dictionary.
    """
    ## Check for AccessErrors
    if not is_token_valid(token):
        raise AccessError(description="Token is not a valid token")

    ## Check for InputErrors
    if not 2 <= len(handle_str) <= 20:
        raise InputError(description="handle_str must be between 2 and 20 characters")
    if is_handle_in_use(handle_str):
        raise InputError(description="Handle is already used by another user")

    ## Find the u_id corresponding to the given token
    user_id = find_u_id(token)

    ## Update the user's details in the database
    auth_data = AUTH_DATABASE.get()
    for user in auth_data["registered_users"]:
        if user["u_id"] == user_id:
            user["handle_str"] = handle_str
            break
    AUTH_DATABASE.update(auth_data)
    return {}
