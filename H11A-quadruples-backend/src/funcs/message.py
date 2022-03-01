"""
Implementations of the message functions.
H11A-quadruples, April 2020.
"""

from datetime import datetime, timezone
import threading
from error import AccessError, InputError
from database.database import MESSAGES_DATABASE
from database.helpers_auth import is_token_valid, find_u_id
from database.helpers_channels import (
    is_user_in_channel,
    is_user_owner,
    does_channel_exist
)
from database.helpers_messages import (
    get_message_id,
    do_sendlater,
    does_message_exist,
    can_user_react,
    has_user_reacted,
    add_react,
    remove_react,
    is_pinned_already,
    did_user_send_message
)
from funcs.hangman import hangman_start, hangman_guess
from constants import VALID_REACT_IDS

def message_send(token, channel_id, message):
    """
    Send a message to a specified channel.

    Args:
        token (str): Token of the user sending the message.
        channel_id (int): id of the channel in which the message is being sent.
        message (str): Message being sent to the channel.
    Raises:
        AccessError: if token is invalid.
        AccessError: if the user making the request is not a member of the given channel.
        InputError: if the message is more than 1000 characters.
        InputError: if a "/hangman" or "/guess" command is used incorrectly.
    Returns:
        A dictionary containing the new message's message_id.
    """
    ## Check for AccessErrors
    if not is_token_valid(token):
        raise AccessError(description="Token is not a valid token")
    if not is_user_in_channel(token, channel_id):
        raise AccessError(description="User has not joined the channel before posting")

    ## Check for InputErrors
    if len(message) > 1000:
        raise InputError(description="Message is more than 1000 characters")

    ## Check for hangman commands
    if message.split()[0] == "/hangman":
        ## first word of the message is '/hangman'
        if len(message.split()) != 1:
            raise InputError(description="'/hangman' takes no other arguments")
        hangman_start(token, channel_id)
        return {}
    if message.split()[0] == "/guess":
        ## first word of the message is '/guess'
        if len(message.split()) != 2:
            raise InputError(description="'/guess' takes one positional argument")
        hangman_guess(token, channel_id, message.split()[1])
        return {}

    ## Generate a message_id for the message
    m_id = get_message_id()

    ## Find the timestamp of the message
    now = datetime.utcnow()
    timestamp = int(now.replace(tzinfo=timezone.utc).timestamp())

    ## Add the message to the database
    messages_data = MESSAGES_DATABASE.get()
    messages_data["messages"].append({
        "channel_id": channel_id,
        "message_id": m_id,
        "u_id": find_u_id(token),
        "message": message,
        "time_created": timestamp,
        "reacts": [], ## no reacts by default
        "is_pinned": False ## not pinned by default
    })
    MESSAGES_DATABASE.update(messages_data)
    return {"message_id": m_id}


def message_sendlater(token, channel_id, message, time_sent):
    """
    Send a message to a specified channel automatically at a specified
    time in the future.

    Args:
        token (str): Token of the user sending the message later.
        channel_id (int): id of the channel in which the message is being sent.
        message (str): Message being sent later to the channel.
        time_sent (int): A UTC UNIX timestamp describing when to send the message.
    Raises:
        AccessError: if token is invalid.
        AccessError: if the user making the request is not a member of the given channel.
        InputError: if channel_id is not a valid channel.
        InputError: if message is more than 1000 characters long.
        InputError: if time_sent is a time in the past.
    Returns:
        A dictionary containing the new message's message_id.
    """
    ## Check for AccessErrors
    if not is_token_valid(token):
        raise AccessError(description="Token is not a valid token")

    ## Check for InputErrors
    if not does_channel_exist(channel_id):
        raise InputError(description="Channel does not exist")
    if len(message) > 1000:
        raise InputError(description="Message is more than 1000 characters")

    ## Check for AccessErrors (..continued)
    if not is_user_in_channel(token, channel_id):
        raise AccessError(description="Only members can post to this channel")

    ## Find the current time
    now = datetime.utcnow()
    time_now = int(now.replace(tzinfo=timezone.utc).timestamp())

    ## Find the interval of time to wait before sending the message
    interval = time_sent - time_now

    ## Check for InputErrors (..continued)
    if interval < 0: ## time_sent is a time in the past
        raise InputError(description="Time sent is a time in the past")

    ## Get the message's id
    m_id = get_message_id()

    ## Add it to the queued_message_ids in the database
    messages_data = MESSAGES_DATABASE.get()
    messages_data["queued_message_ids"].append(m_id)
    MESSAGES_DATABASE.update(messages_data)

    ## Start the timer
    timer = threading.Timer(
        interval, do_sendlater,
        args=[find_u_id(token), channel_id, message, m_id]
    )
    timer.start()

    ## Return the message_id
    return {"message_id": m_id}


def message_react(token, message_id, react_id):
    """
    Add a react to a message in a user's channel.

    Args:
        token (str): Token of the user reacting to the message.
        message_id (int): id of the message being reacted to.
        react_id (int): id of the react that the user is reacting with.
    Raises:
        AccessError: if token is invalid.
        InputError: if message_id is not a valid message in any of the user's channels.
        InputError: if react_id is not a valid react id.
        InputError: if the user has already reacted to the message with the given react_id.
    Returns:
        Empty dictionary.
    """
    ## Assumptions:
    ## - a user can have multiple reacts on one message
    ## - a user cannot react twice with the SAME react_id on the SAME message

    ## Check for AccessErrors
    if not is_token_valid(token):
        raise AccessError(description="Token is not a valid token")

    ## Check for InputErrors
    if react_id not in VALID_REACT_IDS:
        raise InputError(description="react_id is not a valid id")
    if not can_user_react(token, message_id):
        raise InputError(description="Can only react to a message in your channels")
    if has_user_reacted(token, message_id, react_id):
        raise InputError(description="You already reacted to this message with this react")

    ## Add the react information to the database
    messages_data = MESSAGES_DATABASE.get()
    for message in messages_data["messages"]:
        if message["message_id"] == message_id:
            message["reacts"] = add_react(token, react_id, message["reacts"])
            break
    MESSAGES_DATABASE.update(messages_data)
    return {}


def message_unreact(token, message_id, react_id):
    """
    Removes a react from a message in a user's channel.

    Args:
        token (str): Token of the user unreacting to a message.
        message_id (int): id of the message that the user is unreacting to.
        react_id (int): id of the react to remove.
    Raises:
        AccessError: if token is invalid.
        InputError: if message_id is not a valid message in any of the user's channels.
        InputError: if react_id is not a valid react id.
        InputError: if the message does not contain a react by this user with react_id.
    Returns:
        Empty dictionary.
    """
    ## Check for AccessErrors
    if not is_token_valid(token):
        raise AccessError(description="Token is not a valid token")

    ## Check for InputErrors
    if react_id not in VALID_REACT_IDS:
        raise InputError(description="react_id is not a valid id")
    if not has_user_reacted(token, message_id, react_id):
        raise InputError(description="Can only unreact if you have reacted")
    if not can_user_react(token, message_id):
        raise InputError(description="Can only unreact to a message in your channels")

    ## Remove react information from the database
    messages_data = MESSAGES_DATABASE.get()
    for message in messages_data["messages"]:
        if message["message_id"] == message_id:
            message["reacts"] = remove_react(token, react_id, message["reacts"])
            break
    MESSAGES_DATABASE.update(messages_data)
    return {}


def message_pin(token, message_id):
    """
    Mark a message as pinned.

    Args:
        token (str): Token of the user pinning the message.
        message_id (int): id of the message being pinned.
    Raises:
        AccessError: if token is invalid.
        AccessError: if user is not a Slackr owner nor a channel owner.
        AccessError: if the user is not a member of the given chanel.
        InputError: if message_id is not a valid message.
        InputError: if message is already pinned.
    Returns:
        Empty dictionary.
    """
    ## Check for AccessErrors
    if not is_token_valid(token):
        raise AccessError(description="Token is not a valid token")

    ## Check for InputErrors
    if not does_message_exist(message_id):
        raise InputError(description="Message does not exist -- cannot pin")

    ## Message exists, so find its channel_id
    messages_data = MESSAGES_DATABASE.get()
    for message in messages_data["messages"]:
        if message["message_id"] == message_id:
            channel_id = message["channel_id"]
            break

    ## Check for AccessErrors (..continued)
    if not is_user_in_channel(token, channel_id):
        raise AccessError(description="Can only pin messages in a channel you are in")
    if not is_user_owner(token, channel_id):
        raise AccessError(description="Only owners can pin messages")

    ## Check for InputErrors (..continued)
    if is_pinned_already(message_id):
        raise InputError(description="Message is already pinned")

    ## Mark the message as pinned
    for message in messages_data["messages"]:
        if message["message_id"] == message_id:
            message["is_pinned"] = True
            break
    MESSAGES_DATABASE.update(messages_data)
    return {}


def message_unpin(token, message_id):
    """
    Unmark a message as pinned.

    Args:
        token (str): Token of the user unpinning the message.
        message_id (int): id of the message being unpinned.
    Raises:
        AccessError: if token is invalid.
        AccessError: if user is not a Slackr owner nor a channel owner.
        AccessError: if the user is not a member of the given chanel.
        InputError: if message_id is not a valid message.
        InputError: if message is already unpinned.
    Returns:
        Empty dictionary.
    """
    ## Check for AccessErrors
    if not is_token_valid(token):
        raise AccessError(description="Token is not a valid token")

    ## Check for InputErrors
    if not does_message_exist(message_id):
        raise InputError(description="message_id is not a valid message")

    ## Message exists, so find its channel_id
    messages_data = MESSAGES_DATABASE.get()
    for message in messages_data["messages"]:
        if message["message_id"] == message_id:
            channel_id = message["channel_id"]
            break

    ## Check for AccessErrors (..continued)
    if not is_user_in_channel(token, channel_id):
        raise AccessError(description="Can only unpin messages in your channels")
    if not is_user_owner(token, channel_id):
        raise AccessError(description="Only owners can unpin messages")

    ## Check for InputErrors (..continued)
    if not is_pinned_already(message_id):
        raise InputError(description="Message is already unpinned")

    ## Mark the message as unpinned
    for message in messages_data["messages"]:
        if message["message_id"] == message_id:
            message["is_pinned"] = False
            break
    MESSAGES_DATABASE.update(messages_data)
    return {}


def message_remove(token, message_id):
    """
    Remove a message from the channel.

    Args:
        token (str): Token of the user removing the message.
        message_id (int): id of the message being removed.
    Raises:
        AccessError: if token is invalid.
        AccessError: if user is not a Slackr owner nor a channel owner and didn't send the message.
        InputError: if message_id is not a valid message.
    Returns:
        Empty dictionary.
    """
    ## Check for AccessErrors
    if not is_token_valid(token):
        raise AccessError(description="Token is not a valid token")

    ## Check for InputErrors
    if not does_message_exist(message_id):
        raise InputError(description="Message no longer exists")

    ## Remove the message from the database
    messages_data = MESSAGES_DATABASE.get()
    for message in messages_data["messages"]:
        if message["message_id"] == message_id:
            ## Check for AccessErrors (..continued)
            is_owner = is_user_owner(token, message["channel_id"])
            did_send_message = did_user_send_message(token, message_id)
            if not is_owner and not did_send_message:
                raise AccessError(description="Non-owners cannot delete other people's messages")

            ## Add message to removed_messages
            messages_data["removed_messages"].append({
                "channel_id": message["channel_id"],
                "message_id": message_id,
                "u_id": message["u_id"],
                "message": message["message"],
                "time_created": message["time_created"]
            })
            ## Remove the message
            messages_data["messages"].remove(message)
            break
    MESSAGES_DATABASE.update(messages_data)
    return {}


def message_edit(token, message_id, message):
    """
    Update a message with new text. If the new message is an empty string,
    the message is removed.

    Args:
        token (str): Token of the user editing the message.
        message_id (int): id of the message being edited.
    Raises:
        AccessError: if token is invalid.
        AccessError: if user is not a Slackr owner nor a channel owner and didn't send the message.
    Returns:
        Empty dictionary.
    """
    ## Check for AccessErrors
    if not is_token_valid(token):
        raise AccessError(description="Token is not a valid token")

    ## Remove the message if it is an empty string
    if message == "":
        message_remove(token, message_id)
        return {}

    ## Edit the message in the database
    messages_data = MESSAGES_DATABASE.get()
    for message_dict in messages_data["messages"]:
        if message_dict["message_id"] == message_id:
            ## Check for AccessErrors (..continued)
            is_owner = is_user_owner(token, message_dict["channel_id"])
            did_send_message = did_user_send_message(token, message_id)
            if not is_owner and not did_send_message:
                raise AccessError(description="Non-owners cannot edit other people's messages")

            ## Edit the message
            message_dict["message"] = message
            break
    MESSAGES_DATABASE.update(messages_data)
    return {}
