"""
Implementations of the other functions.
H11A-quadruples, April 2020.
"""

import threading
from datetime import datetime, timezone
from error import AccessError, InputError
from database.database import (
    AUTH_DATABASE,
    CHANNELS_DATABASE,
    MESSAGES_DATABASE
)
from database.helpers_auth import (
    reset_auth_data,
    is_token_valid,
    find_u_id,
    is_user_slackr_owner,
    does_user_exist
)
from database.helpers_channels import (
    reset_channels_data,
    is_user_in_channel,
    does_channel_exist,
    is_standup_active
)
from database.helpers_messages import (
    reset_messages_data,
    get_message_id
)
from constants import VALID_PERMISSION_IDS, DELETED_USER_ID

def users_all(token):
    """
    Returns a list of all users and their details.

    Args:
        token (str): Token of the user making the request.
    Raises:
        AccessError: if token is invalid.
    Returns:
        Dictionary containing a list of user dictionaries.
    """
    ## Check for AccessErrors
    if not is_token_valid(token):
        raise AccessError(description="Token is not a valid token")

    users_all_list = {"users": []}
    auth_data = AUTH_DATABASE.get()
    for user in auth_data["registered_users"]:
        users_all_list["users"].append({
            "u_id": user["u_id"],
            "email": user["email"],
            "name_first": user["name_first"],
            "name_last": user["name_last"],
            "handle_str": user["handle_str"],
            "profile_img_url": user["profile_img_url"]
        })
    return users_all_list


def search(token, query_str):
    """
    Return a collection of messages in all of a user's channels that contain
    a given query_str. Messages are sorted from most recent to least recent.

    Args:
        token (str): Token of the user making the search.
        query_str (str): Query to search for.
    Raises:
        AccessError: if token is invalid.
    Returns:
        Dictionary containing a list of messages from the search result.
    """
    ## Check for AccessErrors
    if not is_token_valid(token):
        raise AccessError(description="Token is not a valid token")

    search_result = {"messages": []}
    messages_data = MESSAGES_DATABASE.get()
    for message_dict in messages_data["messages"]:
        if query_str.lower() in message_dict["message"].lower(): ## not case sensitive
            if is_user_in_channel(token, message_dict["channel_id"]):
                ## Find is_this_user_reacted
                new_reacts = message_dict["reacts"]
                user_id = find_u_id(token)
                for react in new_reacts:
                    if user_id in react["u_ids"]:
                        react["is_this_user_reacted"] = True
                    else:
                        react["is_this_user_reacted"] = False

                ## PREPEND the message dictionary so that it is sorted
                ## from most recent to least recent message.
                search_result["messages"].insert(0, {
                    "message_id": message_dict["message_id"],
                    "u_id": message_dict["u_id"],
                    "message": message_dict["message"],
                    "time_created": message_dict["time_created"],
                    "reacts": new_reacts,
                    "is_pinned": message_dict["is_pinned"]
                })
    return search_result


def standup_start(token, channel_id, length):
    """
    Start a standup period in a given channel where for the next "length"
    seconds, if standup_send() is called, message is buffered during the X
    second window. At the end of the window a message will be added to the
    message queue in the channel from the user who started the standup.

    Args:
        token (str): Token of the user starting the standup.
        channel_id (int): id of the channel that the standup is being started in.
        length (int): number of seconds the standup should last.
    Raises:
        AccessError: if token is invalid.
        InputError: if channel_id is not a valid channel.
        InputError: if an active standup is already running in the channel.
    Returns:
        A dictionary containing the time that the standup will finish.
    """
    ## Check for AccessErrors
    if not is_token_valid(token):
        raise AccessError(description="Token is not a valid token")

    ## Check for InputErrors
    if not does_channel_exist(channel_id):
        raise InputError(description="Channel does not exist")
    if is_standup_active(channel_id):
        raise InputError(description="An active standup is currently running in this channel")

    ## Calculate time_finish
    now = datetime.utcnow()
    time_now = int(now.replace(tzinfo=timezone.utc).timestamp())
    time_finish = time_now + length

    ## Change channel info to say that a standup is active
    channels_data = CHANNELS_DATABASE.get()
    for channel in channels_data["channels"]:
        if channel["channel_id"] == channel_id:
            channel["is_standup_active"] = True
            channel["standup_time_finish"] = time_finish
            break
    CHANNELS_DATABASE.update(channels_data)

    ## Start a thread to automatically clear standup_queue
    ## and update is_standup_active and standup_time_finish
    timer = threading.Timer(length, end_standup, args=[find_u_id(token), channel_id])
    timer.start()

    ## Return time_finish
    return {"time_finish": time_finish}


def end_standup(u_id, channel_id):
    """
    Ends a standup by updating channel info in the database and sending the group message.

    Args:
        u_id (int): id of the user who initiated the standup.
        channel_id (int): id of the channel that the standup took place in.
    """
    ## Get list of messages that were sent
    stdup_msgs = []
    channels_data = CHANNELS_DATABASE.get()
    for channel in channels_data["channels"]:
        if channel["channel_id"] == channel_id:
            stdup_msgs = channel["standup_queue"]
            ## Update channel info
            channel["is_standup_active"] = False
            channel["standup_time_finish"] = None
            channel["standup_queue"] = []
            break
    CHANNELS_DATABASE.update(channels_data)

    ## Create the message
    group_message = ""
    for message_tuple in stdup_msgs:
        name, message = message_tuple ## deconstruct
        group_message += f"{name}: {message}\n"

    ## Generate a message_id for the group message
    m_id = get_message_id()

    ## Find the timestamp of the group message
    now = datetime.utcnow()
    timestamp = int(now.replace(tzinfo=timezone.utc).timestamp())

    ## Add the group message to the database
    messages_data = MESSAGES_DATABASE.get()
    messages_data["messages"].append({
        "channel_id": channel_id,
        "message_id": m_id,
        "u_id": u_id,
        "message": group_message,
        "time_created": timestamp,
        "reacts": [],
        "is_pinned": False
    })
    MESSAGES_DATABASE.update(messages_data)


def standup_active(token, channel_id):
    """
    Check whether a standup is active in a given channel and get the time that
    the standup finishes. time_finish is None if a standup is not active.

    Args:
        token (str): Token of the user making the request.
        channel_id (int): id of the channel being checked.
    Raises:
        AccessError: if token is invalid.
        InputError: if channel_id is not a valid channel.
    Returns:
        A dictionary containing whether a standup is active and the time it finishes.
    """
    ## Check for AccessErrors
    if not is_token_valid(token):
        raise AccessError(description="Token is not a valid token")

    ## Check for InputErrors
    if not does_channel_exist(channel_id):
        raise InputError(description="Channel does not exist")

    ## Determine if a standup is active
    channels_data = CHANNELS_DATABASE.get()
    for channel in channels_data["channels"]:
        if channel["channel_id"] == channel_id:
            is_active = channel["is_standup_active"]
            time_finish = channel["standup_time_finish"]
            break

    return {"is_active": is_active, "time_finish": time_finish}


def standup_send(token, channel_id, message):
    """
    Send a message to get buffered in the standup queue.

    Args:
        token (str): Token of the user sending the standup message.
        channel_id (int): id of the channel that the message is being sent to.
        message (str): Message being sent in the standup.
    Raises:
        AccessError: if token is invalid.
        AccessError: if the user is not a member of the given channel.
        InputError: if channel_id is not a valid channel.
        InputError: if message is more than 1000 characters long.
        InputError: if an active standup is not currently running in the channel.
    Returns:
        Empty dictionary.
    """
    ## Check for AccessErrors
    if not is_token_valid(token):
        raise AccessError(description="Token is not a valid token")

    ## Check for InputErrors
    if not does_channel_exist(channel_id):
        raise InputError(description="Channel does not exist")

    ## Check for AccessErrors (..continued)
    if not is_user_in_channel(token, channel_id):
        raise AccessError(description="User is not a member of the channel")

    ## Check for InputErrors (..continued)
    if len(message) > 1000:
        raise InputError(description="Message is more than 1000 characters")
    if not is_standup_active(channel_id):
        raise InputError(description="An active standup is not currently running")

    ## Find the name of the person sending the message
    user_id = find_u_id(token)
    auth_data = AUTH_DATABASE.get()
    for user in auth_data["registered_users"]:
        if user["u_id"] == user_id:
            name_first = user["name_first"]
            break

    ## Add the message to the standup queue in the database
    channels_data = CHANNELS_DATABASE.get()
    for channel in channels_data["channels"]:
        if channel["channel_id"] == channel_id:
            ## Append a tuple (sender, message)
            channel["standup_queue"].append(
                (name_first.lower(), message)
            )
            break
    CHANNELS_DATABASE.update(channels_data)
    return {}


def admin_userpermission_change(token, u_id, permission_id):
    """
    Set a given user's permissions to a given permission_id.

    Args:
        token (str): Token of the user who is setting permissions.
        u_id (int): id of the user whose permissions are being changed.
        permission_id (int): id of the new permission being set.
    Raises:
        AccessError: if token is invalid.
        AccessError: if the user making the request is not a Slackr owner.
        InputError: if u_id is not a valid user.
        InputError: if permission_id is not a valid value.
    Returns:
        Empty dictionary.
    """
    ## Check for AccessErrors
    if not is_token_valid(token):
        raise AccessError(description="Token is not a valid token")

    ## Check for InputErrors
    if not does_user_exist(u_id):
        raise InputError(description="User does not exist")
    if permission_id not in VALID_PERMISSION_IDS:
        raise InputError(description="permission_id is not a valid permission")

    ## Check for AccessErrors (..continued)
    if not is_user_slackr_owner(find_u_id(token)):
        raise AccessError(description="Only Slackr owners can modify user permissions")

    ## Change permission_id in the database
    auth_data = AUTH_DATABASE.get()
    for user in auth_data["registered_users"]:
        if user["u_id"] == u_id:
            user["global_permission_id"] = permission_id
            break
    AUTH_DATABASE.update(auth_data)
    return {}


def admin_user_remove(token, u_id):
    """
    Remove user with u_id from the Slackr.

    Args:
        token (str): Token of the user who is removing another user.
        u_id (int): id of the user being removed.
    Raises:
        AccessError: if token is invalid.
        AccessError: if the user making the request is not a Slackr owner.
        InputError: if u_id does not refer to a valid user.
    Returns:
        Empty dictionary.
    """
    ## Check for AccessErrors
    if not is_token_valid(token):
        raise AccessError(description="Token is not a valid token")
    if not is_user_slackr_owner(find_u_id(token)):
        raise AccessError(description="Only Slackr owners can remove other users")

    ## Check for InputErrors
    if not does_user_exist(u_id):
        raise InputError(description="The user you are trying to remove does not exist")

    ## Update the AUTH_DATABASE
    auth_data = AUTH_DATABASE.get()
    for user in auth_data["registered_users"]:
        if user["u_id"] == u_id:
            ## Add to deleted_users
            auth_data["deleted_users"].append({
                "u_id": u_id,
                "email": user["email"]
            })

            ## Invalidate active token if it exists
            for valid_token in auth_data["active_tokens"]:
                if valid_token["u_id"] == u_id:
                    auth_data["active_tokens"].remove(valid_token)
                    break

            ## Remove from registered users
            auth_data["registered_users"].remove(user)
            break
    AUTH_DATABASE.update(auth_data)

    ## Update the CHANNELS_DATABASE
    channels_data = CHANNELS_DATABASE.get()
    for channel in channels_data["channels"]:
        ## Remove user from channel all_members
        for member in channel["all_members"]:
            if member["u_id"] == u_id:
                channel["all_members"].remove(member)
                break

        ## Remove user from channel owner_members
        for owner in channel["owner_members"]:
            if owner["u_id"] == u_id:
                channel["owner_members"].remove(owner)
                break
    CHANNELS_DATABASE.update(channels_data)

    ## Update the MESSAGES_DATABASE
    messages_data = MESSAGES_DATABASE.get()
    for message in messages_data["messages"]:
        if message["u_id"] == u_id:
            message["u_id"] = DELETED_USER_ID ## reserved u_id for a removed user
    MESSAGES_DATABASE.update(messages_data)

    return {}


def workspace_reset():
    """
    Resets the workspace state.

    Returns:
        Empty dictionary.
    """
    reset_auth_data()
    reset_channels_data()
    reset_messages_data()
    return {}
