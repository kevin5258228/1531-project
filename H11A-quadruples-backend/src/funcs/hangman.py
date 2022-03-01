"""
Implementations of the hangman functions.
H11A-quadruples, April 2020.
"""

import random
from datetime import datetime, timezone
from unicodedata import normalize
from error import InputError
from database.database import CHANNELS_DATABASE, MESSAGES_DATABASE
from database.helpers_auth import find_u_id
from database.helpers_channels import reset_hangman_data
from database.helpers_messages import get_message_id
from helpers.hangman_ascii import HANGMAN_LVLS
from constants import WORD_FILE

WORD_LIST = list(filter(
    lambda word: "'" not in word and len(word) > 4, ## min 4 letter words
    [word.strip() for word in open(WORD_FILE, "r").readlines()]
))

#####################################################################

def normalise_word(word):
    """
    Remove any accents from a given word.

    Args:
        word (str): Word being normalised.
    Returns:
        A string identical to word but with any accents removed.
    """
    return str(normalize("NFD", word).encode("ascii", "ignore").decode("utf-8"))

def get_random_word():
    """
    Returns:
        A randomly generated normalised word from WORD_LIST.
    """
    word = random.choice(WORD_LIST)
    return normalise_word(word)

#####################################################################

def hangman_send(token, channel_id, message):
    """
    Send a hangman-related message to the specified channel.

    Args:
        token (str): Token of the user sending the hangman message.
        channel_id (int): id of the channel in which the message is being sent.
        message (str): Message being sent.
    Returns:
        Dictionary containing the new message's message_id.
    """
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


def hangman_start(token, channel_id):
    """
    Start a hangman game by generating a random word and adding it to
    the database for a given channel. Also sends a welcome message
    to that channel.

    Args:
        token (str): Token of the user starting the hangman game.
        channel_id (int): id of the channel in which the hangman game is being started.
    Raises:
        InputError: if an active hangman game is already running in the channel.
    """
    rand_word = get_random_word()

    ## Add the word to the channel in the channels database
    channels_data = CHANNELS_DATABASE.get()
    for channel in channels_data["channels"]:
        if channel["channel_id"] == channel_id:
            ## Check if a hangman game is already active
            if channel["hangman_word"] is not None:
                raise InputError(description="An active game is already running")
            channel["hangman_word"] = rand_word
            break
    CHANNELS_DATABASE.update(channels_data)

    ## Send the welcome message
    unguessed_word = " ".join(["_" for letter in rand_word])
    welcome_msg = (
        "Welcome to Hangman!\n\n"
        f"Word: {unguessed_word}"
    )
    hangman_send(token, channel_id, welcome_msg)


def hangman_guess(token, channel_id, letter):
    """
    User with given token guesses a letter for the Hangman game running in
    a given channel. Sends a message to the channel indicating the game status.

    Args:
        token (str): Token of the user making the hangman guess.
        channel_id (int): id of the channel in which the hangman guess is being sent.
        letter (str): letter being guessed.
    Raises:
        InputError: if letter is not alphabetical or not of length 1.
        InputError: if a hangman game is not currently active.
        InputError: if letter has already been guessed in the game.
    Returns:
        Nothing if the hangman game is won or lost.
    """
    ## Check if letter is valid
    if len(letter) != 1 or not letter.isalpha():
        raise InputError(description="Enter a single letter to guess")

    channels_data = CHANNELS_DATABASE.get()
    for channel in channels_data["channels"]:
        if channel["channel_id"] == channel_id:
            ## Check if a Hangman game is indeed active
            if channel["hangman_word"] is None:
                raise InputError(description="A hangman game must be active to guess")

            ## Check if letter is already guessed
            if letter.upper() in channel["hangman_guessed"]:
                raise InputError(description=f"'{letter}' has already been guessed.")

            ## If not, add it to the list of guessed letters
            channel["hangman_guessed"].append(letter.upper())

            ## If guess is incorrect, increment the level
            if letter.upper() not in channel["hangman_word"].upper():
                channel["hangman_level"] += 1

            ## Grab data so it can be used
            word = channel["hangman_word"]
            guessed = channel["hangman_guessed"]
            level = channel["hangman_level"]
            break
    CHANNELS_DATABASE.update(channels_data)

    ## Check for game won
    if all([ch in guessed for ch in word.upper()]): ## all letters have been guessed
        game_won_msg = (
            f"{word.upper()}\n"
            "Congratulations! You have won hangman."
        )
        hangman_send(token, channel_id, game_won_msg)
        reset_hangman_data(channel_id)
        return

    ## Check for game lost
    if level == 10: ## game over level
        game_over_msg = (
            f"{word.upper()}\n"
            "You lost!\n\n"
            f"{HANGMAN_LVLS['LVL10']}"
        )
        hangman_send(token, channel_id, game_over_msg)
        reset_hangman_data(channel_id)
        return

    ## Send the game update message if the game is not won or lost
    unguessed_word = " ".join([ch if ch in guessed else "_" for ch in word.upper()])
    level = f"LVL{level}"
    wrong_guesses = " ".join([ch for ch in guessed if ch not in word.upper()])
    game_msg = (
        f"{unguessed_word}\n\n"
        f"{HANGMAN_LVLS[level]}\n"
        f"You have guessed: {wrong_guesses}"
    )
    hangman_send(token, channel_id, game_msg)
