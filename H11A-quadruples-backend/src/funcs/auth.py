"""
Implementations of the auth functions.
H11A-quadruples, April 2020.
"""

from error import AccessError, InputError
from database.database import AUTH_DATABASE
from database.helpers_auth import (
    check_email,
    search_email,
    get_hash,
    check_password,
    generate_token,
    is_token_valid,
    get_u_id,
    get_handle,
    generate_code,
    is_reset_code_valid
)
from helpers.send_email import send_email

def auth_login(email, password):
    """
    Given a registered user's email and password, generate a valid token
    for the user to remain authenticated.

    Args:
        email (str): Email with which the user is logging in.
        password (str): Password user entered to log in.
    Raises:
        InputError: if email is formatted incorrectly.
        InputError: if email does not belong to a registered user.
        InputError: if password is not correct.
    Returns:
        A dictionary containing the user's u_id (int) and a newly generated token (str).
    """
    ## Check for InputErrors
    if not check_email(email):
        raise InputError(description="Email entered is not a valid email")
    if not search_email(email):
        raise InputError(description="Email entered does not belong to a user")
    if not check_password(email, password):
        raise InputError(description="Password is not correct")

    ## If no InputErrors have been raised at this point, then the user's email
    ## is indeed registered and they have entered the correct password

    ## Find the user's id with their given email
    auth_data = AUTH_DATABASE.get()
    for user in auth_data["registered_users"]:
        if user["email"] == email:
            u_id = user["u_id"]

    u_token = generate_token(u_id) ## adds the token to the database
    return {
        "u_id": u_id,
        "token": u_token
    }


def auth_logout(token):
    """
    Invalidate a given active token to log the user out.

    Args:
        token (str): Token to invalidate.
    Raises:
        AccessError: if token is invalid.
    Returns:
        A dictionary indicating if the logout was successful.
    """
    ## Check for AccessErrors
    if not is_token_valid(token):
        raise AccessError(description="Token is not a valid token")

    ## Invalidate the token by removing it from the list of "active_tokens"
    ## in the database
    auth_data = AUTH_DATABASE.get()
    for valid_token in auth_data["active_tokens"]:
        if valid_token["token"] == token:
            auth_data["active_tokens"].remove(valid_token)
            break
    AUTH_DATABASE.update(auth_data)

    ## Check that the user has been successfully logged out
    if not is_token_valid(token):
        ## If the token no longer exists in the database, the logout
        ## is a success
        return {"is_success": True}
    ## Else return is_success: False
    return {"is_success": False}


def auth_register(email, password, name_first, name_last):
    """
    Create a new account for a user and return an active token for
    authentication.

    Args:
        email (str): Email user is registering with.
        password (str): User's password.
        name_first (str): First name of user.
        name_last (str): Last name of user.
    Raises:
        InputError: if email is formatted incorrectly.
        InputError: if email is already in use.
        InputError: if password is less than 6 characters long.
        InputError: if name_first is not between 1 and 50 characters inclusive.
        InputError: if name_last is not between 1 and 50 characters inclusive.
    Returns:
        A dictionary containing a newly generated u_id (int) and token (str).
    """
    ## Check for InputErrors
    if not check_email(email):
        raise InputError(description="Email entered is not a valid email")
    if search_email(email):
        raise InputError(description="Email address is already in use")
    if len(password) < 6:
        raise InputError(description="Password is less than 6 characters long")
    if not 1 <= len(name_first) <= 50:
        raise InputError(description="name_first is not between 1 and 50 characters")
    if not 1 <= len(name_last) <= 50:
        raise InputError(description="name_last is not between 1 and 50 characters")

    ## Determine if the user is the first user to sign up
    auth_data = AUTH_DATABASE.get()
    if auth_data["registered_users"] == []: ## no registered users
        global_permission_id = 1 ## owner
    else:
        global_permission_id = 2 ## member

    ## Generate a token for the user
    u_id = get_u_id()
    u_token = generate_token(u_id)

    ## Register the user by adding their information to the list of
    ## "registered_users" in the database
    from port_settings import BASE_URL
    auth_data["registered_users"].append({
        "u_id": u_id,
        "email": email,
        "name_first": name_first,
        "name_last": name_last,
        "handle_str": get_handle(name_first, name_last),
        "password_hash": get_hash(password),
        "global_permission_id": global_permission_id,
        "reset_code": None,
        "profile_img_url": f"{BASE_URL}/imgurl/default.jpg"
    })
    AUTH_DATABASE.update(auth_data)

    return {
        "u_id": u_id,
        "token": u_token
    }


def auth_passwordreset_request(email):
    """
    Generate a reset code for a forgotten password, then send an email to the user
    containing that code so that they can reset their password. Email is not sent
    if the email is unregistered.

    Args:
        email (str): Email of user who forgot their password.
    Returns:
        Empty dictionary.
    """
    if not search_email(email): ## email not registered
        return {}

    auth_data = AUTH_DATABASE.get()
    for user in auth_data["registered_users"]:
        if user["email"] == email:
            reset_code = generate_code()
            user["reset_code"] = reset_code
            break
    AUTH_DATABASE.update(auth_data)

    send_email(email, reset_code)
    return {}


def auth_passwordreset_reset(reset_code, new_password):
    """
    Reset a given user's password. Removes reset code as it is no longer useful.

    Args:
        reset_code (str): Reset code that the user entered to reset their password.
        new_password (str): New password that the user is trying to set.
    Raises:
        InputError: if reset code is not valid.
        InputError: if new password is less than 6 characters in length.
    Returns:
        Empty dictionary.
    """
    ## Check for InputErrors
    if not is_reset_code_valid(reset_code):
        raise InputError(description="Reset code entered is not valid")
    if len(new_password) < 6:
        raise InputError(description="Password is less than 6 characters long")

    auth_data = AUTH_DATABASE.get()
    for user in auth_data["registered_users"]:
        if user["reset_code"] == reset_code:
            user["password_hash"] = get_hash(new_password)
            user["reset_code"] = None
            break
    return {}
